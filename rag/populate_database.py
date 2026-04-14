from __future__ import annotations

import argparse

from rag.documents import get_document_spec, list_supported_document_ids
from rag.index import rebuild_all_document_databases, rebuild_document_database


def _build_document(document_id: str) -> tuple[str, int]:
    spec = get_document_spec(document_id)
    try:
        chunk_count = rebuild_document_database(document_id)
    except Exception as exc:
        message = str(exc)
        if "not found" in message and "model" in message:
            raise SystemExit(
                "El modelo de embeddings no está disponible en Ollama. "
                "Descarga el modelo predeterminado con `ollama pull bge-m3` "
                "o define OLLAMA_EMBEDDING_MODEL con un modelo de embeddings instalado."
            ) from exc
        raise SystemExit(f"No se pudo construir la base de datos de {spec.pdf_path.name}: {message}") from exc

    return spec.pdf_path.name, chunk_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Reconstruye las bases Chroma para los documentos RAG locales.")
    parser.add_argument(
        "--document",
        choices=list_supported_document_ids(),
        help="Reconstruye solo un documento. Sin este argumento se reconstruyen todos.",
    )
    args = parser.parse_args()

    if args.document:
        pdf_name, chunk_count = _build_document(args.document)
        spec = get_document_spec(args.document)
        print(f"Base de datos Chroma de {pdf_name} construida con {chunk_count} fragmentos en {spec.persist_directory}")
        return

    results = rebuild_all_document_databases()
    for document_id in list_supported_document_ids():
        spec = get_document_spec(document_id)
        chunk_count = results[document_id]
        print(f"Base de datos Chroma de {spec.pdf_path.name} construida con {chunk_count} fragmentos en {spec.persist_directory}")


if __name__ == "__main__":
    main()
