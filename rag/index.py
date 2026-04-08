from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag.loader import load_constitution_documents

VECTOR_STORE_DIR = Path(__file__).resolve().parents[1] / "data" / "vectorstore"
INDEX_PATH = VECTOR_STORE_DIR / "constitution_index.json"
TOKEN_RE = re.compile(r"[A-Za-z0-9']+")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "there",
    "this",
    "to",
    "with",
}

QUERY_EXPANSIONS: dict[str, list[str]] = {
    "articles": ["articulo", "artículos"],
    "assembly": ["asamblea"],
    "citizen": ["ciudadano", "ciudadanía"],
    "citizenship": ["ciudadanía"],
    "congress": ["congreso"],
    "constitution": ["constitución"],
    "court": ["corte"],
    "courts": ["corte"],
    "election": ["elección", "elecciones"],
    "elections": ["elección", "elecciones"],
    "executive": ["ejecutivo"],
    "freedom": ["libertad"],
    "government": ["gobierno"],
    "judge": ["juez", "judicial"],
    "judicial": ["judicial"],
    "law": ["ley", "leyes"],
    "national": ["nacional"],
    "people": ["pueblo"],
    "president": ["presidente"],
    "rights": ["derechos"],
    "senate": ["senado"],
    "senator": ["senador", "senadores"],
    "voting": ["voto", "votar"],
    "vote": ["voto", "votar"],
}


@dataclass(frozen=True)
class ConstitutionChunk:
    text: str
    page: int | None
    source: str
    embedding: dict[str, float]


def _persisted_index_exists() -> bool:
    return INDEX_PATH.exists()


def _split_documents() -> list[Any]:
    documents = load_constitution_documents()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    return splitter.split_documents(documents)


def _tokenize(text: str) -> list[str]:
    tokens = [token.lower() for token in TOKEN_RE.findall(text)]
    return [token for token in tokens if token not in STOPWORDS]


def _normalize_counts(counts: Counter[str]) -> dict[str, float]:
    magnitude = math.sqrt(sum(value * value for value in counts.values()))
    if magnitude == 0.0:
        return {}
    return {token: value / magnitude for token, value in counts.items()}


def _vectorize(text: str) -> dict[str, float]:
    return _normalize_counts(Counter(_tokenize(text)))


def _expand_query(query: str) -> str:
    lowered = query.lower()
    additions: list[str] = []
    for phrase, translations in QUERY_EXPANSIONS.items():
        if phrase in lowered:
            additions.extend(translations)
    if not additions:
        return query
    return f"{query} {' '.join(additions)}"


def _build_chunks() -> list[ConstitutionChunk]:
    chunks = _split_documents()
    records: list[ConstitutionChunk] = []

    for chunk in chunks:
        records.append(
            ConstitutionChunk(
                text=chunk.page_content,
                page=chunk.metadata.get("page"),
                source=str(chunk.metadata.get("source", "constitution.pdf")),
                embedding=_vectorize(chunk.page_content),
            )
        )

    return records


def _write_index(records: list[ConstitutionChunk]) -> None:
    VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
    payload = [asdict(record) for record in records]
    INDEX_PATH.write_text(json.dumps(payload, ensure_ascii=True), encoding="utf-8")


def _read_index() -> list[ConstitutionChunk]:
    payload = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    records: list[ConstitutionChunk] = []
    for item in payload:
        records.append(
            ConstitutionChunk(
                text=item["text"],
                page=item.get("page"),
                source=item.get("source", "constitution.pdf"),
                embedding={str(token): float(weight) for token, weight in item["embedding"].items()},
            )
        )
    return records


def build_constitution_index() -> list[ConstitutionChunk]:
    records = _build_chunks()
    _write_index(records)
    return records


@lru_cache(maxsize=1)
def get_constitution_index() -> list[ConstitutionChunk]:
    if _persisted_index_exists():
        return _read_index()
    return build_constitution_index()


def cosine_similarity(left: dict[str, float], right: dict[str, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(weight * right.get(token, 0.0) for token, weight in left.items())


def retrieve_relevant_chunks(query: str, *, k: int = 4) -> list[ConstitutionChunk]:
    index = get_constitution_index()
    query_vector = _vectorize(_expand_query(query))
    ranked = sorted(
        index,
        key=lambda record: cosine_similarity(query_vector, record.embedding),
        reverse=True,
    )
    return ranked[:k]
