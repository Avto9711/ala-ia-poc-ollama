from __future__ import annotations

from langchain_core.tools import tool

from rag.index import retrieve_relevant_chunks


def _format_chunk(chunk) -> str:
    if chunk.page is None:
        location = "unknown page"
    else:
        location = f"page {chunk.page + 1}"

    return f"[{location}] {chunk.text.strip()}"


def build_constitution_retrieval_tool():
    @tool("retrieve_constitution_context")
    def retrieve_constitution_context(query: str) -> str:
        """Retrieve relevant context from constitution.pdf for a user question."""
        chunks = retrieve_relevant_chunks(query, k=4)

        if not chunks:
            return "No relevant context found in constitution.pdf."

        return "\n\n".join(_format_chunk(chunk) for chunk in chunks)

    return retrieve_constitution_context
