from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class DocumentSpec:
    document_id: str
    title: str
    pdf_path: Path
    persist_directory: Path
    collection_name: str
    tool_name: str
    description: str


SUPPORTED_DOCUMENTS: dict[str, DocumentSpec] = {
    "constitution": DocumentSpec(
        document_id="constitution",
        title="Constitution of the Dominican Republic",
        pdf_path=ROOT_DIR / "constitution.pdf",
        persist_directory=ROOT_DIR / "data" / "chroma" / "constitution",
        collection_name="constitution_pdf",
        tool_name="retrieve_constitution_context",
        description="Recupera contexto relevante de constitution.pdf para preguntas sobre la Constitución de la República Dominicana.",
    ),
    "coopnama_servicios": DocumentSpec(
        document_id="coopnama_servicios",
        title="COOPNAMA Servicios",
        pdf_path=ROOT_DIR / "coopnama-servicios.pdf",
        persist_directory=ROOT_DIR / "data" / "chroma" / "coopnama-servicios",
        collection_name="coopnama_servicios_pdf",
        tool_name="retrieve_coopnama_servicios_context",
        description="Recupera contexto relevante de coopnama-servicios.pdf para preguntas sobre los servicios de COOPNAMA.",
    ),
}


def get_document_spec(document_id: str) -> DocumentSpec:
    try:
        return SUPPORTED_DOCUMENTS[document_id]
    except KeyError as exc:
        available = ", ".join(sorted(SUPPORTED_DOCUMENTS))
        raise KeyError(f"Unknown document_id '{document_id}'. Available documents: {available}") from exc


def list_supported_document_ids() -> list[str]:
    return sorted(SUPPORTED_DOCUMENTS)
