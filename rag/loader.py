from __future__ import annotations

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag.documents import get_document_spec

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 150


def load_pdf_documents(document_id: str):
    spec = get_document_spec(document_id)
    if not spec.pdf_path.exists():
        raise FileNotFoundError(f"Missing PDF source at {spec.pdf_path}")

    loader = PyPDFLoader(str(spec.pdf_path))
    documents = loader.load()

    for document in documents:
        document.metadata.setdefault("source", spec.pdf_path.name)
        document.metadata.setdefault("document_id", spec.document_id)
        document.metadata.setdefault("document_title", spec.title)

    return documents


def split_pdf_documents(
    document_id: str,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
):
    spec = get_document_spec(document_id)
    documents = load_pdf_documents(document_id)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = splitter.split_documents(documents)

    for index, chunk in enumerate(chunks):
        chunk.metadata.setdefault("source", spec.pdf_path.name)
        chunk.metadata.setdefault("document_id", spec.document_id)
        chunk.metadata.setdefault("document_title", spec.title)
        chunk.metadata["chunk_index"] = index

    return chunks


def load_constitution_documents():
    return load_pdf_documents("constitution")


def split_constitution_documents(
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
):
    return split_pdf_documents(
        "constitution",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
