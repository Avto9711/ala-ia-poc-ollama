from __future__ import annotations

from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader

ROOT_DIR = Path(__file__).resolve().parents[1]
CONSTITUTION_PDF_PATH = ROOT_DIR / "constitution.pdf"


def load_constitution_documents():
    if not CONSTITUTION_PDF_PATH.exists():
        raise FileNotFoundError(f"Missing PDF source at {CONSTITUTION_PDF_PATH}")

    loader = PyPDFLoader(str(CONSTITUTION_PDF_PATH))
    documents = loader.load()

    for document in documents:
        document.metadata.setdefault("source", CONSTITUTION_PDF_PATH.name)

    return documents
