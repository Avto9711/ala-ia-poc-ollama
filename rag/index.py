from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
import shutil

import chromadb
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma

from rag.documents import get_document_spec, list_supported_document_ids
from rag.embedding import get_embeddings
from rag.loader import split_pdf_documents

DEFAULT_TOP_K = 4
DEFAULT_SCORE_THRESHOLD = 0.25
DEFAULT_INGEST_BATCH_SIZE = 100


@dataclass(frozen=True)
class RetrievedChunk:
    document: Document
    score: float


def _vector_store(document_id: str) -> Chroma:
    spec = get_document_spec(document_id)
    spec.persist_directory.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(spec.persist_directory))
    return Chroma(
        collection_name=spec.collection_name,
        persist_directory=str(spec.persist_directory),
        client=client,
        embedding_function=get_embeddings(),
    )


def _collection_count(vector_store: Chroma) -> int:
    collection = getattr(vector_store, "_collection", None)
    if collection is None:
        return 0
    return int(collection.count())


def _ingest_batch_size() -> int:
    return max(1, int(os.getenv("RAG_INGEST_BATCH_SIZE", str(DEFAULT_INGEST_BATCH_SIZE))))


def _chunk_id(document_id: str, document: Document, index: int) -> str:
    page = document.metadata.get("page")
    if isinstance(page, int):
        page_part = f"page-{page + 1}"
    else:
        page_part = "page-unknown"
    return f"{document_id}-{page_part}-chunk-{index}"


def _seed_vector_store(document_id: str, vector_store: Chroma) -> int:
    documents = split_pdf_documents(document_id)
    batch_size = _ingest_batch_size()
    for start in range(0, len(documents), batch_size):
        batch_documents = documents[start : start + batch_size]
        batch_ids = [
            _chunk_id(document_id, document, index)
            for index, document in enumerate(batch_documents, start=start)
        ]
        vector_store.add_documents(documents=batch_documents, ids=batch_ids)
    return len(documents)


def rebuild_document_database(document_id: str) -> int:
    spec = get_document_spec(document_id)
    get_vector_store.cache_clear()
    if spec.persist_directory.exists():
        shutil.rmtree(spec.persist_directory)

    fresh_vector_store = _vector_store(document_id)
    return _seed_vector_store(document_id, fresh_vector_store)


@lru_cache(maxsize=None)
def get_vector_store(document_id: str) -> Chroma:
    try:
        vector_store = _vector_store(document_id)
        if _collection_count(vector_store) == 0:
            _seed_vector_store(document_id, vector_store)
        return vector_store
    except Exception:
        # Recover from incompatible or corrupted local Chroma state by rebuilding it.
        rebuild_document_database(document_id)
        return _vector_store(document_id)


def rebuild_all_document_databases() -> dict[str, int]:
    return {document_id: rebuild_document_database(document_id) for document_id in list_supported_document_ids()}


def rebuild_constitution_database() -> int:
    return rebuild_document_database("constitution")


def get_constitution_vector_store() -> Chroma:
    return get_vector_store("constitution")


def retrieve_relevant_chunks(
    document_id: str,
    query: str,
    *,
    k: int = DEFAULT_TOP_K,
    score_threshold: float = DEFAULT_SCORE_THRESHOLD,
) -> list[RetrievedChunk]:
    if not query.strip():
        return []

    spec = get_document_spec(document_id)
    vector_store = get_vector_store(document_id)

    best_by_key: dict[str, RetrievedChunk] = {}
    results = vector_store.similarity_search_with_relevance_scores(query, k=k)
    for document, score in results:
        if score < score_threshold:
            continue

        page = document.metadata.get("page")
        source = str(document.metadata.get("source", spec.pdf_path.name))
        chunk_index = document.metadata.get("chunk_index")
        key = f"{document_id}:{source}:{page}:{chunk_index}:{document.page_content[:120]}"
        current = best_by_key.get(key)
        candidate = RetrievedChunk(document=document, score=float(score))

        if current is None or candidate.score > current.score:
            best_by_key[key] = candidate

    ranked = sorted(best_by_key.values(), key=lambda item: item.score, reverse=True)
    return ranked[:k]
