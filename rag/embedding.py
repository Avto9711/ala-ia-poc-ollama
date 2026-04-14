from __future__ import annotations

import os
from functools import lru_cache

import httpx
from langchain_ollama import OllamaEmbeddings

DEFAULT_EMBEDDING_MODEL = "bge-m3"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"


def _embedding_model_name() -> str:
    return os.getenv("OLLAMA_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)


def _ollama_base_url() -> str | None:
    return os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL)


@lru_cache(maxsize=1)
def ensure_embedding_model_available() -> None:
    base_url = _ollama_base_url()
    if not base_url:
        return

    tags_url = f"{base_url.rstrip('/')}/api/tags"
    try:
        response = httpx.get(tags_url, timeout=5.0)
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:  # pragma: no cover - surface runtime setup issues clearly
        raise RuntimeError(
            f"Could not verify Ollama models at {tags_url}. "
            f"Check that the Ollama server is running."
        ) from exc

    model_names = set()
    for model in payload.get("models", []):
        name = model.get("name")
        model_name = model.get("model")
        if isinstance(name, str):
            model_names.add(name)
        if isinstance(model_name, str):
            model_names.add(model_name)

    embedding_model = _embedding_model_name()
    if embedding_model not in model_names and f"{embedding_model}:latest" not in model_names:
        raise RuntimeError(
            f"Embedding model '{embedding_model}' is not installed in Ollama. "
            f"Pull it first with `ollama pull {embedding_model}` and then rebuild the "
            f"constitution database with `uv run python -m rag.populate_database`."
        )


@lru_cache(maxsize=1)
def get_embeddings() -> OllamaEmbeddings:
    ensure_embedding_model_available()
    kwargs: dict[str, object] = {"model": _embedding_model_name()}
    base_url = _ollama_base_url()
    if base_url:
        kwargs["base_url"] = base_url
    return OllamaEmbeddings(**kwargs)
