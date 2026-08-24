"""Builds a FAISS FlatL2 index over all jobs using all-MiniLM-L6-v2 embeddings.

Uses the same ONNX Runtime pipeline as the live service (app/services/embedding_service.py)
so the offline-built index and the runtime query encoder always produce identical vector
spaces. This also means running this script never requires installing PyTorch, keeping
the whole pipeline - ingest, embed, and serve - torch-free.
"""
import argparse
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import faiss  # noqa: E402
from tqdm import tqdm  # noqa: E402

from app.db.database import get_connection, init_schema  # noqa: E402
from app.services import embedding_service  # noqa: E402

EMBED_BATCH_SIZE = 100
EMBEDDING_DIM = embedding_service.EMBEDDING_DIM


def build_job_text(row) -> str:
    parts = [row["title"] or "", row["skills"] or "", row["domain"] or "", (row["description"] or "")[:500]]
    return " | ".join(p for p in parts if p)


def generate_embeddings(db_path_override=None, index_path_override=None):
    conn = get_connection()
    init_schema(conn)

    faiss_index_path = index_path_override or os.environ.get(
        "FAISS_INDEX_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "jobs.faiss")
    )
    faiss_index_path = os.path.abspath(faiss_index_path)
    os.makedirs(os.path.dirname(faiss_index_path), exist_ok=True)

    index = faiss.IndexFlatL2(EMBEDDING_DIM)

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as c FROM jobs")
    total = cursor.fetchone()["c"]

    cursor.execute("DELETE FROM vector_mappings")
    conn.commit()

    offset = 0
    faiss_pos = 0
    write_cursor = conn.cursor()

    with tqdm(total=total, desc="Embedding jobs") as pbar:
        while True:
            cursor.execute(
                "SELECT job_id, title, skills, domain, description FROM jobs ORDER BY job_id LIMIT ? OFFSET ?",
                (EMBED_BATCH_SIZE, offset),
            )
            rows = cursor.fetchall()
            if not rows:
                break

            texts = [build_job_text(r) for r in rows]
            vectors = embedding_service.embed_texts(texts)
            index.add(vectors)

            mapping_batch = [(faiss_pos + i, r["job_id"]) for i, r in enumerate(rows)]
            write_cursor.executemany(
                "INSERT OR REPLACE INTO vector_mappings (faiss_index, job_id) VALUES (?, ?)",
                mapping_batch,
            )
            conn.commit()

            faiss_pos += len(rows)
            offset += EMBED_BATCH_SIZE
            pbar.update(len(rows))

    faiss.write_index(index, faiss_index_path)
    conn.close()
    return {"total_embedded": faiss_pos, "index_path": faiss_index_path, "dim": EMBEDDING_DIM}


def main():
    parser = argparse.ArgumentParser(description="Generate FAISS embeddings for all jobs in SQLite.")
    parser.parse_args()
    result = generate_embeddings()
    print(result)


if __name__ == "__main__":
    main()
