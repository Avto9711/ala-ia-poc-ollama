from __future__ import annotations

from langchain_core.tools import tool

from rag.documents import get_document_spec
from rag.index import retrieve_relevant_chunks


def _format_chunk(chunk) -> str:
    page = chunk.document.metadata.get("page")
    if isinstance(page, int):
        location = f"page {page + 1}"
    else:
        location = "unknown page"

    document_title = str(
        chunk.document.metadata.get("document_title", chunk.document.metadata.get("source", "document"))
    )
    score = f"{chunk.score:.3f}"
    text = chunk.document.page_content.strip()
    return f"[{document_title} | {location} | score {score}] {text}"


def build_document_retrieval_tool(document_id: str):
    spec = get_document_spec(document_id)

    @tool(spec.tool_name, description=spec.description)
    def retrieve_document_context(query: str) -> str:
        chunks = retrieve_relevant_chunks(document_id, query, k=4)
        if not chunks:
            return f"No se encontró contexto relevante en {spec.pdf_path.name}."

        return "\n\n".join(_format_chunk(chunk) for chunk in chunks)

    return retrieve_document_context


def build_constitution_retrieval_tool():
    return build_document_retrieval_tool("constitution")


def build_coopnama_servicios_retrieval_tool():
    return build_document_retrieval_tool("coopnama_servicios")
