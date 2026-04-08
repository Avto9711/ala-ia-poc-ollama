# POC Plan: FastMCP API Wrapper + Constitution RAG

## Goal

Build a proof of concept where the agent in `main.py` can:

1. Call a local MCP server that wraps the public endpoints from `https://restful-api.dev/`.
2. Retrieve grounded information from `constitution.pdf` through a simple RAG pipeline.

Constraints:

- Keep the current generation model in place (`ChatOllama` with `gemma4-e4b-m1-16gb`).
- Reuse the repo's current ecosystem where possible, which today means building around LangChain and Ollama rather than introducing a separate agent framework.
- Optimize for the smallest working vertical slice, not production hardening.

## Current Repo Baseline

- `main.py` is a minimal synchronous `ChatOllama` invocation.
- The repo already depends on LangChain and LangChain Ollama.
- There is no existing MCP server, no agent loop, and no retrieval/indexing pipeline yet.

This means the POC should first convert `main.py` from a direct model call into a tool-capable LangChain agent entrypoint, then attach:

- MCP tools from a local FastMCP server.
- A local RAG retrieval tool backed by `constitution.pdf`.

## Recommended Architecture

### 1. External API integration: MCP server

Use FastMCP to expose a narrow wrapper around `https://restful-api.dev/` as MCP tools.

Why:

- This is the cleanest place to use MCP.
- LangChain already has an MCP adapter path via `langchain-mcp-adapters`.
- The API surface is small and public, so it is a good fit for a simple read-focused tool server.

### 2. Constitution lookup: local LangChain RAG tool

Implement the RAG path as a local LangChain tool instead of a second MCP server.

Why:

- It reuses the existing LangChain stack already in the repo.
- It keeps the POC smaller and easier to debug.
- The agent can consume both MCP tools and ordinary LangChain tools in the same `create_agent(...)` call.

If the POC works and consistency becomes more important later, the RAG tool can be promoted into MCP as a follow-up.

## Proposed Files

- `main.py`
  - Refactor into an async LangChain agent entrypoint.
  - Load MCP tools from the FastMCP server.
  - Register the local RAG retrieval tool.
- `servers/restful_api_mcp.py`
  - FastMCP server exposing the selected `restful-api.dev` endpoints.
- `rag/loader.py`
  - PDF loading and chunking logic for `constitution.pdf`.
- `rag/index.py`
  - Build and persist the vector index locally.
- `rag/retriever.py`
  - Retrieval function used by the agent tool.
- `rag/__init__.py`
  - Small exports only.
- `data/vectorstore/`
  - Local persisted vector store files.
- `docs/` or root-level notes
  - Short setup and run instructions after implementation.

For a small repo like this, keeping the first cut flat is also acceptable. If speed matters more than structure, `rag.py` plus `servers/restful_api_mcp.py` is enough for the first pass.

## Dependency Changes

Add the minimum packages needed for the POC:

- `fastmcp`
- `langchain-mcp-adapters`
- `langchain-community`
- `langchain-text-splitters`
- `langchain-chroma`
- `chromadb`
- `pypdf`
- `httpx`

Optional but likely useful:

- `langchain-ollama` is already present and can supply embeddings via `OllamaEmbeddings`.

Notes:

- Do not change the generation model in `main.py`.
- Using an Ollama embedding model is acceptable because embeddings are part of retrieval infrastructure, not a change to the answer-generation model.
- For the POC, prefer a local persistent vector store such as Chroma over a custom file format.

## Implementation Phases

## Phase 1: Refactor `main.py` into a tool-capable agent

Target outcome:

- `main.py` becomes the orchestration entrypoint instead of a direct `model.invoke(...)` script.

Steps:

1. Keep `ChatOllama(model="gemma4-e4b-m1-16gb", temperature=0.2)` as the generation model.
2. Switch to a LangChain agent created with `create_agent(...)`.
3. Make `main.py` async so it can use `MultiServerMCPClient`.
4. Load MCP tools from a local stdio server process.
5. Merge those MCP tools with a local RAG tool list.
6. Invoke the agent with a normal chat message interface.

Definition of done:

- A single question can trigger either the REST tool or the RAG tool from the same agent entrypoint.

## Phase 2: Create the FastMCP wrapper for `restful-api.dev`

Target outcome:

- A local FastMCP server exposes a narrow, predictable set of read operations against the public API.

Recommended MCP tools for the POC:

- `list_objects()`
- `get_object_by_id(object_id: str)`
- `list_objects_by_ids(ids: list[str])`

Potential stretch tool:

- `create_object(name: str, data: dict)`

POC recommendation:

- Start read-only first.
- Only add create/update/delete after the basic agent loop is stable.

Implementation notes:

- Use `httpx` inside the FastMCP tool functions.
- Normalize base URL handling in one helper.
- Return compact JSON-safe dictionaries.
- Surface HTTP failures as readable tool errors.
- Run the server over stdio from `main.py` using `python servers/restful_api_mcp.py`.

Definition of done:

- The MCP server can be started locally.
- `main.py` can discover its tools through `langchain-mcp-adapters`.
- The agent can answer a prompt such as "Fetch object 7 from restful-api.dev".

## Phase 3: Build the Constitution RAG index

Target outcome:

- `constitution.pdf` is chunked, embedded, and stored in a local vector database.

Recommended pipeline:

1. Load `constitution.pdf` with a LangChain PDF loader.
2. Split with `RecursiveCharacterTextSplitter`.
3. Generate embeddings with `OllamaEmbeddings`.
4. Persist into a local Chroma collection under `data/vectorstore/`.

Practical defaults for the first pass:

- Chunk size: about `800-1200`
- Chunk overlap: about `100-200`
- Top-k retrieval: `3-5`

Indexing strategy:

- Build a small standalone indexing command, for example `python -m rag.index`.
- Rebuild only when the source PDF changes.
- Keep persistence on disk so `main.py` does not re-embed on every run.

Definition of done:

- A local retrieval call returns relevant chunks for a question grounded in `constitution.pdf`.

## Phase 4: Expose RAG retrieval as an agent tool

Target outcome:

- The agent can call a local tool to retrieve constitution context before answering.

Recommended interface:

- A LangChain `@tool` such as `retrieve_constitution_context(query: str) -> str`

Behavior:

- Run similarity search on the persisted vector store.
- Serialize top matches into a compact string with metadata such as page number or chunk id.
- Instruct the agent to use this tool when the user asks about the constitution or PDF contents.

Why keep this local for now:

- No transport overhead.
- Easier debugging for the first working POC.
- Uses the same LangChain tool mechanism the repo is already centered on.

Definition of done:

- The agent can answer a question like "What does the constitution say about X?" using retrieved context instead of generic model knowledge.

## Phase 5: Compose the final agent behavior in `main.py`

Target outcome:

- One entrypoint, one model, two tool sources.

Composition plan:

1. Initialize the Ollama chat model exactly as today.
2. Start a `MultiServerMCPClient` config that points at `servers/restful_api_mcp.py` over stdio.
3. Load MCP tools with `await client.get_tools()`.
4. Build the local RAG retrieval tool.
5. Pass `mcp_tools + [retrieve_constitution_context]` into `create_agent(...)`.
6. Add a short system prompt that tells the agent:
   - use the REST MCP tools for `restful-api.dev` questions,
   - use the constitution retrieval tool for PDF/content questions,
   - avoid inventing retrieved facts when the tool returns no support.

Definition of done:

- The agent uses the proper tool based on user intent and answers in a single execution path.

## Phase 6: Smoke tests for the POC

Target outcome:

- Enough verification to prove the concept works end to end.

Test cases:

1. API tool path:
   - Ask for a known object by id.
   - Ask to list objects.
2. RAG path:
   - Ask a question whose answer is clearly in `constitution.pdf`.
   - Verify the answer reflects retrieved content.
3. Tool selection:
   - Ask one API question and one constitution question in sequence.
4. Failure handling:
   - Ask for a missing object id.
   - Ask an out-of-scope constitution question and verify the agent does not fabricate confidence.

For the POC, manual smoke tests are enough unless the implementation is simple enough to add a tiny automated test layer.

## Suggested Execution Order

1. Add dependencies.
2. Refactor `main.py` into an async LangChain agent shell.
3. Implement the FastMCP server with one read tool.
4. Verify MCP tool discovery from `main.py`.
5. Build the PDF indexing pipeline.
6. Add the RAG retrieval tool.
7. Tune the prompt so the agent uses the right tool.
8. Run end-to-end smoke tests.

This order reduces debugging ambiguity because MCP connectivity and RAG indexing can each be validated independently before combining them.

## Scope Guardrails

Keep these out of the first POC unless they are required:

- Multi-document ingestion.
- Hybrid retrieval.
- Reranking.
- Streaming UI.
- MCP-authenticated remote deployment.
- Write operations against `restful-api.dev` beyond a simple demo.
- Model changes or prompt-engineering experiments unrelated to tool integration.

## Risks and Mitigations

### Risk: MCP integration adds async complexity

Mitigation:

- Move `main.py` to `asyncio.run(main())` early and keep the rest of the orchestration simple.

### Risk: PDF extraction quality is noisy

Mitigation:

- Start with straightforward PDF extraction and validate chunk quality before tuning retriever settings.

### Risk: Embeddings require an Ollama embedding model that is not yet available locally

Mitigation:

- Treat embedding model setup as an explicit prerequisite in the README/update notes.
- Keep the chat model unchanged.

### Risk: Tool selection is inconsistent

Mitigation:

- Use a short, explicit system prompt describing when each tool should be used.
- Keep tool names and descriptions unambiguous.

## Deliverable for the POC

The POC is successful when:

- Running `main.py` starts an agent that still uses `gemma4-e4b-m1-16gb`.
- The agent can call a FastMCP-backed wrapper around `restful-api.dev`.
- The agent can retrieve grounded context from `constitution.pdf`.
- Both capabilities work from the same entrypoint without changing the model.

## Recommended First Cut

If we want the smallest useful implementation, build exactly this:

1. `servers/restful_api_mcp.py` with:
   - `list_objects`
   - `get_object_by_id`
2. `rag/index.py` to embed `constitution.pdf` into Chroma.
3. `rag/retriever.py` with one `retrieve_constitution_context` tool.
4. `main.py` refactored to:
   - keep `ChatOllama`,
   - load MCP tools through `MultiServerMCPClient`,
   - register the RAG tool,
   - run a single interactive or single-prompt invocation.

That is the fastest path to proving both tool channels work end to end.
