"""Builds a stratified-sample subset of jobs.db + a matching jobs.faiss for deployment.

Local dev keeps the full dataset (backend/data/jobs.db, jobs.faiss) untouched.
This script writes a separate, smaller pair of files under backend/data/deploy/
sized to comfortably fit inside Render free tier's 512MB RAM limit, sampled
proportionally across `domain` and `source` so the deployed demo still looks
representative of the full dataset.
"""
import argparse
import os
import random
import sqlite3
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SRC_DB = os.path.join(os.path.dirname(__file__), "..", "data", "jobs.db")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "deploy")
OUT_DB = os.path.join(OUT_DIR, "jobs.db")
OUT_FAISS = os.path.join(OUT_DIR, "jobs.faiss")

TABLE_SCHEMA = """
CREATE TABLE jobs (
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


def pick_job_ids(src_conn, target_total: int) -> list:
    cursor = src_conn.cursor()
    cursor.execute("SELECT domain, source, COUNT(*) c FROM jobs GROUP BY domain, source")
    groups = cursor.fetchall()
    grand_total = sum(g["c"] for g in groups)

    chosen = []
    rng = random.Random(42)
    for g in groups:
        domain, source, count = g["domain"], g["source"], g["c"]
        quota = max(1, round(target_total * count / grand_total))
        cursor.execute(
            "SELECT job_id FROM jobs WHERE domain IS ? AND source IS ? ORDER BY job_id",
            (domain, source),
        )
        ids = [r["job_id"] for r in cursor.fetchall()]
        rng.shuffle(ids)
        chosen.extend(ids[:quota])
    return chosen


def build_dataset(target_total: int):
    os.makedirs(OUT_DIR, exist_ok=True)
    for path in (OUT_DB, OUT_FAISS):
        if os.path.exists(path):
            os.remove(path)

    src_conn = sqlite3.connect(SRC_DB)
    src_conn.row_factory = sqlite3.Row

    job_ids = pick_job_ids(src_conn, target_total)
    print(f"Selected {len(job_ids)} jobs out of source total for deploy subset.")

    out_conn = sqlite3.connect(OUT_DB)
    out_conn.execute(TABLE_SCHEMA)
    out_conn.execute(
        """
        CREATE VIRTUAL TABLE jobs_fts USING fts5(
            job_id UNINDEXED,
            title,
            company_name,
            description,
            skills
        );
        """
    )
    out_conn.execute(
        """
        CREATE TABLE vector_mappings (
            faiss_index INTEGER PRIMARY KEY,
            job_id TEXT UNIQUE NOT NULL,
            FOREIGN KEY (job_id) REFERENCES jobs(job_id)
        );
        """
    )
    out_conn.execute("CREATE TABLE ingestion_meta (key TEXT PRIMARY KEY, value TEXT);")
    out_conn.execute("CREATE INDEX idx_jobs_source ON jobs(source);")
    out_conn.execute("CREATE INDEX idx_jobs_location ON jobs(location);")
    out_conn.execute("CREATE INDEX idx_jobs_exp ON jobs(experience_min, experience_max);")
    out_conn.execute("CREATE INDEX idx_jobs_fingerprint ON jobs(fingerprint);")

    cols = [
        "job_id", "company_name", "title", "description", "formatted_description",
        "location", "source", "posted_at", "salary_min", "salary_max",
        "experience_min", "experience_max", "skills", "apply_link", "domain",
        "employment_type", "fingerprint", "created_at",
    ]
    col_list = ", ".join(cols)
    placeholders = ", ".join(["?"] * len(cols))

    src_cursor = src_conn.cursor()
    batch = []
    for job_id in job_ids:
        src_cursor.execute(f"SELECT {col_list} FROM jobs WHERE job_id = ?", (job_id,))
        row = src_cursor.fetchone()
        if row:
            batch.append(tuple(row[c] for c in cols))

    out_conn.executemany(f"INSERT INTO jobs ({col_list}) VALUES ({placeholders})", batch)
    out_conn.executemany(
        "INSERT INTO jobs_fts (job_id, title, company_name, description, skills) VALUES (?, ?, ?, ?, ?)",
        [(r[0], r[2], r[1], r[3], r[12]) for r in batch],
    )
    out_conn.commit()
    out_conn.close()
    src_conn.close()

    print(f"Wrote {len(batch)} rows to {OUT_DB}")


def main():
    parser = argparse.ArgumentParser(description="Build a trimmed jobs dataset for deployment.")
    parser.add_argument("--target", type=int, default=10000, help="Target number of jobs in the deploy subset.")
    args = parser.parse_args()
    build_dataset(args.target)


if __name__ == "__main__":
    main()
