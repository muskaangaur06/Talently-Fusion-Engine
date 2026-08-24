"""Verifies SQLite WAL mode, FTS5 indexing, and FAISS vector index consistency."""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import DB_PATH, get_connection, init_schema  # noqa: E402
from app.services import embedding_service  # noqa: E402


def check_wal_mode(conn) -> bool:
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode;")
    mode = cursor.fetchone()[0]
    print(f"[WAL check] journal_mode = {mode}")
    return mode.lower() == "wal"


def check_fts5_table(conn) -> bool:
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs_fts'")
    exists = cursor.fetchone() is not None
    print(f"[FTS5 check] jobs_fts table exists = {exists}")
    if not exists:
        return False
    cursor.execute("SELECT COUNT(*) FROM jobs_fts")
    fts_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM jobs")
    jobs_count = cursor.fetchone()[0]
    print(f"[FTS5 check] jobs_fts rows = {fts_count}, jobs rows = {jobs_count}")
    return fts_count == jobs_count


def check_faiss_consistency(conn) -> bool:
    index = embedding_service.get_index()
    if index is None:
        print("[FAISS check] No index file found (run generate_embeddings.py first)")
        return False
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM vector_mappings")
    mapping_count = cursor.fetchone()[0]
    print(f"[FAISS check] index.ntotal = {index.ntotal}, vector_mappings rows = {mapping_count}")
    return index.ntotal == mapping_count


def main():
    print(f"Database path: {DB_PATH}")
    conn = get_connection()
    init_schema(conn)

    results = {
        "wal_mode": check_wal_mode(conn),
        "fts5_indexed": check_fts5_table(conn),
        "faiss_consistent": check_faiss_consistency(conn),
    }
    conn.close()

    print("\n=== Verification Summary ===")
    all_passed = True
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"{name}: {status}")
        all_passed = all_passed and passed

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
