# Plan: Replace Current Lexical RAG With a Pixegami-Style LangChain RAG

## Goal

Implement a RAG pipeline in this repo that follows the same core strategy as `pixegami/langchain-rag-tutorial`, but adapted to this project's constraints:

- keep the current generation model in place: `ChatOllama(model="gemma4-e4b-m1-16gb")`
- use `constitution.pdf` as the knowledge source
- preserve the current agent shape in [agent_runtime.py](/Users/angeltorres/source/llm-local-exploration/agent_runtime.py)
- expose retrieval as a tool the agent can call
- support both the CLI in [main.py](/Users/angeltorres/source/llm-local-exploration/main.py) and the Chainlit UI in [ui.py](/Users/angeltorres/source/llm-local-exploration/ui.py)

## What The Pixegami Tutorial Does

The reference repo uses a straightforward LangChain RAG structure:

1. Load source files from disk.
2. Split them into chunks with `RecursiveCharacterTextSplitter`.
3. Build a persistent Chroma vector database.
4. At query time, run similarity search against Chroma.
5. Assemble a prompt using the retrieved context.
6. Ask the LLM to answer only from that context.

The current repo does not do that. Its retrieval in [rag/index.py](/Users/angeltorres/source/llm-local-exploration/rag/index.py) is a lexical token index with manual query expansion. This plan replaces that retrieval path with a persistent vector-store workflow modeled on the Pixegami structure.

## Target Architecture

### Ingestion path

- Load [constitution.pdf](/Users/angeltorres/source/llm-local-exploration/constitution.pdf)
- Split the PDF into chunks with `RecursiveCharacterTextSplitter`
- Embed those chunks with an Ollama embedding model
- Persist them in a local Chroma directory

### Query path

- Load the existing Chroma database
- Run similarity search for the user question
- Return top matching chunks as context
- Let the agent answer using that retrieved context

### Agent integration

- Keep the retrieval exposed as `retrieve_constitution_context`
- Continue registering that tool in [agent_runtime.py](/Users/angeltorres/source/llm-local-exploration/agent_runtime.py)
- Keep the FastMCP API server unchanged in [servers/restful_api_mcp.py](/Users/angeltorres/source/llm-local-exploration/servers/restful_api_mcp.py)

## Recommended File Changes

### Keep

- [main.py](/Users/angeltorres/source/llm-local-exploration/main.py)
- [ui.py](/Users/angeltorres/source/llm-local-exploration/ui.py)
- [agent_runtime.py](/Users/angeltorres/source/llm-local-exploration/agent_runtime.py)
- [servers/restful_api_mcp.py](/Users/angeltorres/source/llm-local-exploration/servers/restful_api_mcp.py)
- [rag/loader.py](/Users/angeltorres/source/llm-local-exploration/rag/loader.py)

### Replace or refactor

- [rag/index.py](/Users/angeltorres/source/llm-local-exploration/rag/index.py)
  - replace lexical token indexing with Chroma-based persistence and retrieval
- [rag/retriever.py](/Users/angeltorres/source/llm-local-exploration/rag/retriever.py)
  - keep the tool API, but switch implementation to vector search results

### Add

- `rag/embedding.py`
  - centralize embedding model configuration
- `rag/populate_database.py`
  - explicit ingestion command, similar to Pixegami's `create_database.py`
- optionally `rag/query_debug.py`
  - small CLI for retrieval-only debugging without running the full agent

## Dependency Changes

To follow the Pixegami approach in this repo's ecosystem, add:

- `langchain-chroma`
- `chromadb`

Likely keep:

- `langchain`
- `langchain-community`
- `langchain-ollama`
- `langchain-text-splitters`
- `pypdf`

Recommended embedding choice for this repo:

- `OllamaEmbeddings`

Reason:

- It stays local
- It fits the current Ollama-based stack
- It avoids introducing OpenAI dependencies that the Pixegami tutorial uses

Suggested default embedding model:

- `nomic-embed-text`

Make that configurable via environment variable:

- `OLLAMA_EMBEDDING_MODEL`

## Implementation Phases

## Phase 1: Introduce a proper vector-store ingestion step

Target:

- Separate document ingestion from document querying, matching the Pixegami structure.

Tasks:

1. Create `rag/populate_database.py`.
2. Load [constitution.pdf](/Users/angeltorres/source/llm-local-exploration/constitution.pdf) via [rag/loader.py](/Users/angeltorres/source/llm-local-exploration/rag/loader.py).
3. Split with `RecursiveCharacterTextSplitter`.
4. Create stable chunk metadata:
   - `source`
   - `page`
   - `chunk_id`
5. Build a Chroma collection under `data/chroma`.
6. Persist the database locally.

Definition of done:

- Running a single command creates a persistent Chroma database from the constitution PDF.

## Phase 2: Replace lexical retrieval with Chroma retrieval

Target:

- [rag/index.py](/Users/angeltorres/source/llm-local-exploration/rag/index.py) becomes the retrieval interface over Chroma instead of a custom token index.

Tasks:

1. Remove:
   - manual tokenization
   - manual query expansion
   - custom cosine similarity over token weights
   - JSON index persistence as the primary retrieval path
2. Add functions to:
   - create/load the Chroma database
   - run `similarity_search_with_relevance_scores(...)`
   - return top `k` documents
3. Define a minimum relevance threshold for "no answer found".

Suggested first-pass defaults:

- `k=4`
- chunk size `800-1000`
- overlap `100-150`
- relevance threshold to be tuned empirically after testing

Definition of done:

- A retrieval-only query returns the top semantically similar constitution chunks from Chroma.

## Phase 3: Keep the tool API stable

Target:

- The rest of the app should not need large changes.

Tasks:

1. Keep `build_constitution_retrieval_tool()` in [rag/retriever.py](/Users/angeltorres/source/llm-local-exploration/rag/retriever.py).
2. Change the tool internals so it formats documents returned by Chroma.
3. Include metadata in the formatted context:
   - page number
   - source
   - optionally relevance score

Definition of done:

- [agent_runtime.py](/Users/angeltorres/source/llm-local-exploration/agent_runtime.py) continues to work without interface changes.

## Phase 4: Improve grounding instructions

Target:

- Use the Pixegami pattern of "answer from context only", but in an agent-compatible form.

Tasks:

1. Update the system prompt in [agent_runtime.py](/Users/angeltorres/source/llm-local-exploration/agent_runtime.py) so it clearly says:
   - use `retrieve_constitution_context` for constitution questions
   - answer from returned context when present
   - say when the retrieved context is insufficient
2. Optionally format retrieval results with separators between chunks for cleaner prompting.

Definition of done:

- The model is less likely to answer from generic prior knowledge when constitution context should be used.

## Phase 5: Add explicit ingestion and debugging commands

Target:

- Make the RAG path easy to rebuild and inspect.

Tasks:

1. Add a documented command such as:
   - `uv run python -m rag.populate_database`
2. Optionally add:
   - a retrieval-only debug CLI
   - a flag to rebuild the database from scratch

Definition of done:

- A developer can rebuild the index without touching the UI or full agent path.

## Phase 6: Update docs

Target:

- The README should explain the new architecture accurately.

Tasks:

1. Remove the current description of lexical retrieval.
2. Replace it with:
   - chunking
   - Ollama embeddings
   - Chroma persistence
   - similarity search at query time
3. Document the prerequisite that an embedding model must exist in Ollama locally.

Definition of done:

- The README matches the implemented code rather than the current stopgap RAG design.

## Recommended Code Shape

### `rag/embedding.py`

Purpose:

- one place to configure the embedding model

Suggested responsibilities:

- read `OLLAMA_EMBEDDING_MODEL`
- return `OllamaEmbeddings(...)`

### `rag/populate_database.py`

Purpose:

- explicit ingestion script

Suggested responsibilities:

- load documents
- split documents
- clear or update Chroma
- persist data

### `rag/index.py`

Purpose:

- runtime retrieval helpers

Suggested responsibilities:

- open Chroma
- run similarity search
- return documents and scores

### `rag/retriever.py`

Purpose:

- convert retrieved documents into tool-friendly text for the agent

Suggested responsibilities:

- call `rag.index`
- apply threshold handling
- serialize top chunks

## Suggested Test Plan

### Retrieval-only validation

Run a retrieval query directly and inspect top chunks for:

- presidential qualifications
- term length
- vice president requirements
- judicial or congressional references

### Agent-level validation

Test questions such as:

1. "What are the qualifications for President according to the constitution?"
2. "What does the constitution say about the Vice President?"
3. "Fetch object 7 from restful-api.dev."
4. "What are the qualifications for President and also fetch object 7?"

Expected outcomes:

- constitution questions use the retrieval tool
- REST questions use the MCP tool
- mixed questions may require one or both tools, depending on prompting and model behavior

### Negative tests

1. Ask a constitution question with no clear answer in the PDF
2. Verify the tool returns weak/no context cleanly
3. Verify the final answer does not fabricate certainty

## Risks

### Risk: Ollama runtime instability

This repo already has a local Ollama startup issue. That affects both generation and embeddings if the embedding model also runs through Ollama.

Mitigation:

- treat Ollama health as a prerequisite
- test retrieval helper functions separately from the full agent where possible

### Risk: PDF extraction quality

If the PDF text is noisy, embeddings will still inherit that noise.

Mitigation:

- inspect extracted chunks before indexing
- consider small cleanup rules if the PDF extraction is visibly messy

### Risk: Chroma dependency friction on macOS

The Pixegami tutorial explicitly notes environment friction around Chroma-related dependencies.

Mitigation:

- add setup notes to the README
- validate the dependency install path in this repo before switching the default RAG implementation

## Recommended Execution Order

1. Add Chroma dependencies.
2. Implement `rag/embedding.py`.
3. Add `rag/populate_database.py`.
4. Refactor [rag/index.py](/Users/angeltorres/source/llm-local-exploration/rag/index.py) to use Chroma retrieval.
5. Update [rag/retriever.py](/Users/angeltorres/source/llm-local-exploration/rag/retriever.py) to format Chroma results.
6. Rebuild the constitution database.
7. Test retrieval without the full agent first.
8. Validate the agent path through [main.py](/Users/angeltorres/source/llm-local-exploration/main.py) and [ui.py](/Users/angeltorres/source/llm-local-exploration/ui.py).
9. Update the README.

## Success Criteria

This migration is successful when:

- the repo uses a persistent Chroma store instead of the current lexical JSON index
- constitution retrieval is embedding-based and semantically stronger than token overlap
- the retrieval tool API remains stable for the agent
- both CLI and Chainlit continue to work without architectural rewrites
- the implementation stays local-first and does not change the generation model

## Source Reference

This plan is based on the structure and approach shown in:

- Pixegami repository: https://github.com/pixegami/langchain-rag-tutorial
- GitHub README summary and repository layout
- `create_database.py` and `query_data.py` structure from that repository
