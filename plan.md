# Plan: Integrate `coopnama-servicios.pdf` Into The RAG System

## Goal

Add the new PDF, `coopnama-servicios.pdf`, as a retrievable knowledge source so the agent can use it the same way it currently uses `constitution.pdf`.

The current code does not support that cleanly because the RAG path is hardcoded around one document:

- `rag/loader.py` only knows about `constitution.pdf`
- `rag/index.py` only manages one Chroma collection and one persist directory
- `rag/retriever.py` only exposes `retrieve_constitution_context`
- `agent_runtime.py` only instructs the model to use the constitution tool
- `rag/populate_database.py` only rebuilds the constitution database

## Recommended Approach

Do a small generalization of the existing RAG layer instead of adding a second copy-pasted pipeline.

That means:

1. Keep the constitution flow working.
2. Introduce a document registry/configuration layer for supported PDFs.
3. Reuse the same ingestion and retrieval code for both PDFs.
4. Expose one additional retrieval tool for the new document.

This is the lowest-risk path because it matches the current architecture while avoiding a second set of document-specific modules.

## Implementation Steps

### 1. Add a document registry

Create a small source of truth for supported PDFs, for example in a new file such as `rag/documents.py`.

Suggested contents:

- logical document id, for example `constitution` and `coopnama_servicios`
- display name / agent-facing description
- PDF path
- Chroma persist directory
- collection name
- tool name

Expected outcome:

- the app stops hardcoding constitution-only metadata across multiple files
- new documents can be added by configuration instead of by cloning code paths

### 2. Generalize loading and chunking

Refactor `rag/loader.py` so it can load and split any registered PDF, not only the constitution.

Suggested shape:

- replace `load_constitution_documents()` with something like `load_pdf_documents(document_id: str)`
- replace `split_constitution_documents()` with something like `split_pdf_documents(document_id: str, ...)`
- ensure chunk metadata includes:
  - `source`
  - `document_id`
  - `document_title`
  - `page`
  - `chunk_index`

Expected outcome:

- both PDFs produce chunks with consistent metadata
- retrieval formatting can identify which document a chunk came from

### 3. Generalize vector-store creation and querying

Refactor `rag/index.py` so the vector store is parameterized by `document_id`.

Suggested changes:

- replace single constants like `PERSIST_DIRECTORY` and `COLLECTION_NAME`
- add helpers such as:
  - `get_vector_store(document_id: str)`
  - `rebuild_document_database(document_id: str)`
  - `retrieve_relevant_chunks(document_id: str, query: str, ...)`
- generate chunk ids using the document id, not only `constitution-...`
- keep one Chroma directory per document, for example:
  - `data/chroma/constitution`
  - `data/chroma/coopnama_servicios`

Expected outcome:

- each PDF has isolated persistence
- rebuilding one document does not wipe the other

### 4. Add a retrieval tool for the new PDF

Refactor `rag/retriever.py` so tool-building is generic.

Suggested shape:

- create a generic helper like `build_document_retrieval_tool(document_id: str)`
- keep `build_constitution_retrieval_tool()` as a thin wrapper for compatibility
- add `build_coopnama_servicios_retrieval_tool()`

Suggested new tool name:

- `retrieve_coopnama_servicios_context`

Suggested tool description:

- clarify that it retrieves context from `coopnama-servicios.pdf`
- mention the document topic in Spanish if known from the PDF contents

Expected outcome:

- the agent can explicitly retrieve evidence from the new PDF
- the existing constitution tool continues working

### 5. Wire the new tool into the agent

Update `agent_runtime.py` to register both retrieval tools.

Changes:

- import the new tool builder
- pass both RAG tools into `create_agent(...)`
- update `SYSTEM_PROMPT` so the model knows:
  - when to use `retrieve_constitution_context`
  - when to use `retrieve_coopnama_servicios_context`
  - not to invent facts if neither tool returns support

Expected outcome:

- the agent has access to the new PDF at runtime
- tool selection is guided explicitly instead of relying on guesswork

### 6. Update the rebuild command

Refactor `rag/populate_database.py` so it can build either one document or all registered documents.

Recommended behavior:

- default: rebuild all registered PDF databases
- optional CLI argument or env var to rebuild one document only

Examples:

- `uv run python -m rag.populate_database`
- `uv run python -m rag.populate_database --document coopnama_servicios`

Expected outcome:

- the new PDF gets embedded and persisted without manual code edits
- future documents use the same ingestion command

### 7. Update exports and README

Update:

- `rag/__init__.py`
- `README.md`
- any UI text that currently mentions only `constitution.pdf`

Documentation should include:

- that the app now supports both PDFs
- how to rebuild both vector stores
- example prompts for the new document
- where each Chroma database is stored

Also update user-facing copy in:

- `ui.py`
- `main.py` if it prints help text or examples

### 8. Verify end-to-end behavior

Run at least these checks:

1. Static validation
   - `uv run python -m py_compile main.py agent_runtime.py ui.py rag/*.py servers/*.py`
   - `uv run ruff check main.py agent_runtime.py ui.py rag servers`
2. Rebuild databases
   - rebuild the constitution database
   - rebuild the new PDF database
3. Retrieval-only tests
   - invoke the constitution tool directly
   - invoke the new PDF tool directly
4. Full agent tests
   - ask a constitution question
   - ask a `coopnama-servicios.pdf` question
   - ask one mixed multi-tool question and verify the agent uses the correct source

## File-Level Change List

- `rag/documents.py`
  - new registry/config for supported PDFs
- `rag/loader.py`
  - generalize PDF loading and chunking
- `rag/index.py`
  - generalize Chroma persistence and retrieval by document id
- `rag/retriever.py`
  - generic tool builder plus new tool for `coopnama-servicios.pdf`
- `rag/populate_database.py`
  - rebuild one or all registered documents
- `rag/__init__.py`
  - export both tool builders or the generic builder
- `agent_runtime.py`
  - register the new tool and update system instructions
- `README.md`
  - document the second PDF and rebuild flow
- `ui.py`
  - update prompt hints if needed
- `main.py`
  - update CLI examples/help text if needed

## Acceptance Criteria

- asking about the constitution still uses retrieved constitution context
- asking about `coopnama-servicios.pdf` returns grounded context from that PDF
- both PDFs have separate persisted Chroma stores
- rebuilding one PDF does not delete the other
- the agent prompt clearly describes when to use each retrieval tool
- docs and usage examples reflect the new multi-document setup

## Notes

- Avoid duplicating the existing constitution pipeline into `loader_coopnama.py`, `index_coopnama.py`, etc. That would work short-term but will make every future document more expensive to add.
- Keep the first refactor narrow: support multiple registered PDFs, not an arbitrary upload system.
- If the new PDF has a different language or formatting style, verify chunk quality before tuning retrieval thresholds.
