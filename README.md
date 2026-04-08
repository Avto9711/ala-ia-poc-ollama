# llm-local-exploration

Local proof of concept for an agent that can:

- call a FastMCP wrapper around the public `restful-api.dev` object endpoints
- retrieve grounded context from `constitution.pdf`
- answer through the existing Ollama chat model in this repo

## Components

- [main.py](/Users/angeltorres/source/llm-local-exploration/main.py): CLI entrypoint for a single prompt
- [ui.py](/Users/angeltorres/source/llm-local-exploration/ui.py): Chainlit browser UI
- [agent_runtime.py](/Users/angeltorres/source/llm-local-exploration/agent_runtime.py): shared agent wiring
- [servers/restful_api_mcp.py](/Users/angeltorres/source/llm-local-exploration/servers/restful_api_mcp.py): FastMCP server for `restful-api.dev`
- [rag/loader.py](/Users/angeltorres/source/llm-local-exploration/rag/loader.py): PDF loading
- [rag/index.py](/Users/angeltorres/source/llm-local-exploration/rag/index.py): local constitution index
- [rag/retriever.py](/Users/angeltorres/source/llm-local-exploration/rag/retriever.py): retrieval tool exposed to the agent

## Model

The generation model is unchanged:

- `gemma4-e4b-m1-16gb`

The agent is built around `ChatOllama` and will also start the local MCP server subprocess when needed.

## Requirements

- Python `>=3.10`
- `uv`
- a working local Ollama runtime
- the Ollama model `gemma4-e4b-m1-16gb`

If Ollama is broken locally, the CLI and UI will both fail during inference even if the rest of the repo is correct.

## Install Dependencies

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv sync
```

## Run The CLI

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run python main.py "Fetch object 7 from restful-api.dev"
```

Example constitution question:

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run python main.py "What are the qualifications for President according to the constitution?"
```

## Run The Browser UI

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run chainlit run ui.py --host 127.0.0.1 --port 8000
```

Then open:

- `http://localhost:8000`

Chainlit may log macOS browser-launch errors in this environment when it tries to auto-open a browser. Those messages do not prevent the app from running.

## Data And Indexing

- The source document is [constitution.pdf](/Users/angeltorres/source/llm-local-exploration/constitution.pdf)
- The local index is created on first retrieval under `data/vectorstore/constitution_index.json`
- The current retrieval path is a lightweight lexical index with small query expansion for the constitution text

This is enough for the POC, but it is not a semantic-grade RAG system.

## How The RAG Works

The retrieval path in this repo is intentionally simple and local.

1. The user sends a prompt through [main.py](/Users/angeltorres/source/llm-local-exploration/main.py) or [ui.py](/Users/angeltorres/source/llm-local-exploration/ui.py).
2. Both entrypoints call into [agent_runtime.py](/Users/angeltorres/source/llm-local-exploration/agent_runtime.py), which builds the LangChain agent and registers the `retrieve_constitution_context` tool from [rag/retriever.py](/Users/angeltorres/source/llm-local-exploration/rag/retriever.py).
3. When the agent needs grounded constitution context, that tool calls `retrieve_relevant_chunks(...)` in [rag/index.py](/Users/angeltorres/source/llm-local-exploration/rag/index.py).
4. On first use, [rag/index.py](/Users/angeltorres/source/llm-local-exploration/rag/index.py) loads [constitution.pdf](/Users/angeltorres/source/llm-local-exploration/constitution.pdf) via [rag/loader.py](/Users/angeltorres/source/llm-local-exploration/rag/loader.py), splits it into chunks, tokenizes the text, and builds a normalized word-frequency representation for each chunk.
5. That chunk index is persisted to `data/vectorstore/constitution_index.json` so it does not need to be rebuilt on every request.
6. For a query, the code tokenizes the question, applies a small English-to-Spanish query expansion map, and computes cosine similarity between the query token weights and each chunk's token weights.
7. The top matching chunks are returned with page numbers.
8. The agent uses those returned chunks as context for the final answer.

Important implementation detail:

- This is retrieval over a lexical token index, not an embedding-based vector store.
- It does not use Chroma, FAISS, or semantic embeddings.
- It works well enough for the current POC because the document set is small and fixed, but it is a pragmatic shortcut rather than a production RAG design.

## Verification

Useful checks:

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run python -m py_compile main.py agent_runtime.py ui.py rag/*.py servers/*.py
env UV_CACHE_DIR=/tmp/uv-cache uv run ruff check main.py agent_runtime.py ui.py rag servers
```

## Current Limitation

The main blocker on this machine is Ollama itself. If `ollama` crashes during startup, tool wiring and retrieval can still be valid, but end-to-end responses will fail until the local Ollama runtime is fixed.
