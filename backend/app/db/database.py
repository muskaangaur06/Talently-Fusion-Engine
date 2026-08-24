import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "..", "..", "data", "jobs.db"))
DB_PATH = os.path.abspath(DB_PATH)


def get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


@contextmanager
def db_session():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_schema(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            company_name TEXT,
            title TEXT,
            description TEXT,
            formatted_description TEXT,
            location TEXT,
            source TEXT,
            posted_at TEXT,
            salary_min REAL,
            salary_max REAL,
            experience_min INTEGER,
            experience_max INTEGER,
            skills TEXT,
            apply_link TEXT,
            domain TEXT,
            employment_type TEXT,
            fingerprint TEXT,
            created_at TEXT
        );
        """
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_exp ON jobs(experience_min, experience_max);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_fingerprint ON jobs(fingerprint);")
    cursor.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS jobs_fts USING fts5(
            job_id UNINDEXED,
            title,
            company_name,
            description,
            skills
        );
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS vector_mappings (
            faiss_index INTEGER PRIMARY KEY,
            job_id TEXT UNIQUE NOT NULL,
            FOREIGN KEY (job_id) REFERENCES jobs(job_id)
        );
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ingestion_meta (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """
    )
    conn.commit()
