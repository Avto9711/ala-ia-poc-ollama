# llm-local-exploration

Proof of concept for a local agent that can:

- call public `restful-api.dev` endpoints through a FastMCP tool server
- retrieve grounded context from [constitution.pdf](/Users/angeltorres/source/llm-local-exploration/constitution.pdf) and [coopnama-servicios.pdf](/Users/angeltorres/source/llm-local-exploration/coopnama-servicios.pdf)
- answer with the existing Ollama chat model

## Overview

This repo has two user-facing entrypoints:

- [main.py](/Users/angeltorres/source/llm-local-exploration/main.py): CLI for a single prompt
- [ui.py](/Users/angeltorres/source/llm-local-exploration/ui.py): Chainlit browser UI

Both call [agent_runtime.py](/Users/angeltorres/source/llm-local-exploration/agent_runtime.py), which builds one LangChain agent with:

- `ChatOllama(model="gemma4-e4b-m1-16gb")`
- MCP tools loaded from [servers/restful_api_mcp.py](/Users/angeltorres/source/llm-local-exploration/servers/restful_api_mcp.py)
- local RAG tools from [rag/retriever.py](/Users/angeltorres/source/llm-local-exploration/rag/retriever.py)

## RAG Path

The retrieval path lives under [rag/](/Users/angeltorres/source/llm-local-exploration/rag):

- [rag/documents.py](/Users/angeltorres/source/llm-local-exploration/rag/documents.py): registry of supported PDFs
- [rag/loader.py](/Users/angeltorres/source/llm-local-exploration/rag/loader.py): loads and chunks PDFs
- [rag/embedding.py](/Users/angeltorres/source/llm-local-exploration/rag/embedding.py): configures `OllamaEmbeddings`
- [rag/index.py](/Users/angeltorres/source/llm-local-exploration/rag/index.py): opens and queries the Chroma vector stores
- [rag/retriever.py](/Users/angeltorres/source/llm-local-exploration/rag/retriever.py): exposes retrieval as LangChain tools
- [rag/populate_database.py](/Users/angeltorres/source/llm-local-exploration/rag/populate_database.py): rebuilds the vector databases

Each supported PDF has its own Chroma persistence directory:

- `data/chroma/constitution`
- `data/chroma/coopnama-servicios`

The agent uses:

- `retrieve_constitution_context` for constitution questions
- `retrieve_coopnama_servicios_context` for COOPNAMA services questions

## Models

Chat model:

- `gemma4-e4b-m1-16gb`

Embedding model:

- `nomic-embed-text`

You can override the embedding model with `OLLAMA_EMBEDDING_MODEL` and the Ollama base URL with `OLLAMA_BASE_URL`.

## Setup

### 1. Install Ollama

Install Ollama for your OS using the official docs:

- macOS: https://docs.ollama.com/macos
- Linux: https://docs.ollama.com/linux
- Windows: https://docs.ollama.com/windows

After install, make sure the local Ollama server is available:

```bash
ollama -v
ollama list
```

If you installed the standalone Linux package, start the server first:

```bash
ollama serve
```

### 2. Install Python Dependencies

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv sync
```

### 3. Create The Local Chat Model From `Modelfile`

This repo expects the chat model name `gemma4-e4b-m1-16gb`. The included [Modelfile](/Users/angeltorres/source/llm-local-exploration/Modelfile) builds that local model from the Ollama base model `gemma4:e4b`.

Pull the base model, then create the local named model:

```bash
ollama pull gemma4:e4b
ollama create gemma4-e4b-m1-16gb -f ./Modelfile
```

You can verify that the model was created:

```bash
ollama list
ollama run gemma4-e4b-m1-16gb
```

### 4. Pull The Embedding Model

The RAG pipeline also needs an embedding model:

```bash
ollama pull nomic-embed-text
```

### 5. Build The RAG Databases

Rebuild both registered PDFs:

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run python -m rag.populate_database
```

Rebuild one document only:

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run python -m rag.populate_database --document constitution
env UV_CACHE_DIR=/tmp/uv-cache uv run python -m rag.populate_database --document coopnama_servicios
```

### 6. Run The App

CLI:

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run python main.py "Fetch object 7 from restful-api.dev"
env UV_CACHE_DIR=/tmp/uv-cache uv run python main.py "¿Cuáles son los requisitos para ser Presidente según la Constitución?"
env UV_CACHE_DIR=/tmp/uv-cache uv run python main.py "¿Qué servicios ofrece COOPNAMA según el PDF?"
```

Browser UI:

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run chainlit run ui.py --host 127.0.0.1 --port 8000
```

### 7. Test Retrieval Directly

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run python -c 'from rag.retriever import build_constitution_retrieval_tool; tool = build_constitution_retrieval_tool(); print(tool.invoke({"query": "¿Cuáles son los requisitos para ser Presidente?"}))'
env UV_CACHE_DIR=/tmp/uv-cache uv run python -c 'from rag.retriever import build_coopnama_servicios_retrieval_tool; tool = build_coopnama_servicios_retrieval_tool(); print(tool.invoke({"query": "¿Qué servicios ofrece COOPNAMA?"}))'
```

## End-To-End Quickstart

For a clean machine, the shortest path is:

```bash
ollama pull gemma4:e4b
ollama create gemma4-e4b-m1-16gb -f ./Modelfile
ollama pull nomic-embed-text
env UV_CACHE_DIR=/tmp/uv-cache uv sync
env UV_CACHE_DIR=/tmp/uv-cache uv run python -m rag.populate_database
env UV_CACHE_DIR=/tmp/uv-cache uv run chainlit run ui.py --host 127.0.0.1 --port 8000
```

Then open `http://127.0.0.1:8000`.

## Verification

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run python -m py_compile main.py agent_runtime.py ui.py rag/*.py servers/*.py
env UV_CACHE_DIR=/tmp/uv-cache uv run ruff check main.py agent_runtime.py ui.py rag servers
```

## Notes

- Spanish queries will usually retrieve better because both PDFs are Spanish-language documents.
- The CLI and UI share the same agent runtime, so behavior should be consistent.
- If `ollama run gemma4-e4b-m1-16gb` fails, recreate the local model with `ollama create gemma4-e4b-m1-16gb -f ./Modelfile`.
- If the Ollama chat model or embedding model is missing, the agent or rebuild commands will fail until Ollama is fixed locally.
