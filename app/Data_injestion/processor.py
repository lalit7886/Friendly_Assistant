import os
import json
import numpy as np
from pathlib import Path

from app.services.retrieval.embeddings import embed_texts
from app.Data_injestion.loader.excel import read_excel_


PROCESSED_DATA_DIR = "processed_data"


def save_embeddings(
    embeddings,
    chunks,
    filename: str,
    output_dir: str = PROCESSED_DATA_DIR
):
    output_dir = Path(output_dir)

    embedding_dir = output_dir / "embeddings"
    chunk_dir = output_dir / "chunks"

    embedding_dir.mkdir(parents=True, exist_ok=True)
    chunk_dir.mkdir(parents=True, exist_ok=True)

    embeddings_array = np.asarray(embeddings, dtype=np.float32)

    embedding_path = (
        embedding_dir /
        f"{Path(filename).stem}.npy"
    )

    np.save(embedding_path, embeddings_array)

    chunk_path = (
        chunk_dir /
        f"{Path(filename).stem}.json"
    )

    with open(chunk_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    return embedding_path, chunk_path


def process_excel(file_path: str, filename: str):
    chunks = read_excel_(file_path)

    if not chunks:
        raise ValueError("No chunks found in Excel file")

    embeddings = embed_texts(chunks)

    if len(embeddings) != len(chunks):
        raise ValueError(
            f"Embedding count ({len(embeddings)}) "
            f"does not match chunk count ({len(chunks)})"
        )

    embeddings = np.asarray(embeddings, dtype=np.float32)

    embedding_path, chunk_path = save_embeddings(
        embeddings,
        chunks,
        filename
    )

    return embedding_path, chunk_path


if __name__ == "__main__":
    file_path = "/Users/lalitramanmishra/RAG/RAG_PROJ_1/DATA/improved1.xlsx"

    embedding_path, chunk_path = process_excel(
        file_path,
        Path(file_path).name
    )

    print(f"Embeddings saved to: {embedding_path}")
    print(f"Chunks saved to: {chunk_path}")
    
