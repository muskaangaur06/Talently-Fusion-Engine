"""Memory-safe streaming ingestion of the raw jobs JSON export into SQLite.

Streams the source array with ijson (never loads the full file into memory),
normalizes/deduplicates records, and writes them to SQLite (+ FTS5) in
batches of 100. Safe for multi-hundred-MB source files under low RAM.
"""
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

import ijson
from tqdm import tqdm

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import get_connection, init_schema  # noqa: E402

BATCH_SIZE = 500

SOURCE_KEYWORDS = [
    ("linkedin", "LinkedIn"),
    ("naukri", "Naukri"),
    ("indeed", "Indeed"),
    ("internshala", "Internshala"),
]


def _double_json_decode(raw):
    """apply_options / salaries arrive as JSON-encoded strings (sometimes
    double-encoded with escaped quotes). Decode defensively."""
    if raw is None:
        return None
    if not isinstance(raw, str):
        return raw
    raw = raw.strip()
    if raw == "" or raw.lower() == "null":
        return None
    try:
        decoded = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    if isinstance(decoded, str):
        try:
            decoded = json.loads(decoded)
        except (json.JSONDecodeError, TypeError):
            return None
    return decoded


def detect_source(via: str, apply_options_raw) -> str:
    via_lower = (via or "").lower()
    for keyword, label in SOURCE_KEYWORDS:
        if keyword in via_lower:
            return label

    apply_opts = _double_json_decode(apply_options_raw)
    if isinstance(apply_opts, list):
        blob = json.dumps(apply_opts).lower()
        for keyword, label in SOURCE_KEYWORDS:
            if keyword in blob:
                return label

    return "Unknown"


def extract_salary(salaries_raw):
    salaries = _double_json_decode(salaries_raw)
    if isinstance(salaries, list) and salaries:
        first = salaries[0]
        if isinstance(first, dict):
            return first.get("salary_from"), first.get("salary_to")
    return None, None


def extract_apply_link(apply_options_raw) -> str:
    apply_opts = _double_json_decode(apply_options_raw)
    if isinstance(apply_opts, list) and apply_opts:
        first = apply_opts[0]
        if isinstance(first, dict):
            return first.get("link", "") or ""
    return ""


def safe_int(value):
    try:
        if value is None or value == "" or value == "null":
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def safe_float(value):
    try:
        if value is None or value == "" or value == "null":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def make_fingerprint(company_name: str, title: str, location: str) -> str:
    key = f"{(company_name or '').strip().lower()}|{(title or '').strip().lower()}|{(location or '').strip().lower()}"
    return hashlib.md5(key.encode("utf-8")).hexdigest()


PLACEHOLDER_VALUES = {"not mentioned", "not specified", "n/a", "na", "none", "null", "-"}


def _is_placeholder(value: str) -> bool:
    return value.strip().lower() in PLACEHOLDER_VALUES


def clean_and_normalize(job: dict) -> dict:
    company_name = job.get("company_name") or "Unknown"
    title = job.get("title") or job.get("roles") or "Untitled Role"
    location = job.get("location") or "Not specified"

    salary_min, salary_max = extract_salary(job.get("salaries"))
    source = detect_source(job.get("via", ""), job.get("apply_options"))
    apply_link = extract_apply_link(job.get("apply_options"))

    skills_raw = job.get("skills") or ""
    if isinstance(skills_raw, list):
        skill_items = [str(s).strip() for s in skills_raw]
    else:
        skill_items = [s.strip() for s in str(skills_raw).split(",")]
    skills = ", ".join(s for s in skill_items if s and not _is_placeholder(s))

    return {
        "job_id": job.get("job_id"),
        "company_name": company_name.strip(),
        "title": title.strip(),
        "description": job.get("description") or "",
        "formatted_description": job.get("formattedDescription") or job.get("description") or "",
        "location": location.strip(),
        "source": source,
        "posted_at": job.get("posted_at") or job.get("publishedAt") or "",
        "salary_min": safe_float(salary_min),
        "salary_max": safe_float(salary_max),
        "experience_min": safe_int(job.get("minExperienceRequired")),
        "experience_max": safe_int(job.get("maxExperienceRequired")),
        "skills": skills,
        "apply_link": apply_link,
        "domain": job.get("domain") or "",
        "employment_type": job.get("employmentType") or job.get("schedule_type") or "",
        "fingerprint": make_fingerprint(company_name, title, location),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def upsert_batch(conn, batch: list) -> None:
    """Writes only to the plain jobs table. jobs_fts is rebuilt in one bulk pass
    at the end of ingest() instead of being kept in sync per-batch, since FTS5
    incremental updates get progressively slower as the index grows and dominate
    ingestion time on a large file."""
    if not batch:
        return
    cursor = conn.cursor()
    cursor.executemany(
        """
        INSERT OR REPLACE INTO jobs (
            job_id, company_name, title, description, formatted_description,
            location, source, posted_at, salary_min, salary_max,
            experience_min, experience_max, skills, apply_link, domain,
            employment_type, fingerprint, created_at
        ) VALUES (
            :job_id, :company_name, :title, :description, :formatted_description,
            :location, :source, :posted_at, :salary_min, :salary_max,
            :experience_min, :experience_max, :skills, :apply_link, :domain,
            :employment_type, :fingerprint, :created_at
        )
        """,
        batch,
    )
    conn.commit()


def rebuild_fts_index(conn) -> None:
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jobs_fts")
    cursor.execute(
        """
        INSERT INTO jobs_fts (job_id, title, company_name, description, skills)
        SELECT job_id, title, company_name, description, skills FROM jobs
        """
    )
    conn.commit()


def load_existing_dedup_state(conn) -> tuple:
    """Seeds dedup sets from rows already in the DB, so re-running ingestion against
    new or updated source data (incremental/live feeds) won't create duplicate rows
    for jobs already stored from a previous run."""
    cursor = conn.cursor()
    cursor.execute("SELECT job_id, fingerprint FROM jobs")
    job_ids = set()
    fingerprints = set()
    for row in cursor.fetchall():
        job_ids.add(row["job_id"])
        if row["fingerprint"]:
            fingerprints.add(row["fingerprint"])
    return job_ids, fingerprints


def ingest(input_path: str, limit: int = None) -> dict:
    conn = get_connection()
    init_schema(conn)
    conn.execute("PRAGMA synchronous=OFF;")

    seen_job_ids, seen_fingerprints = load_existing_dedup_state(conn)
    preexisting_job_count = len(seen_job_ids)
    batch = []
    stats = {"total_seen": 0, "inserted": 0, "duplicate_job_id": 0, "duplicate_fingerprint": 0, "skipped_no_id": 0}

    file_size = os.path.getsize(input_path)
    with open(input_path, "rb") as f, tqdm(total=file_size, unit="B", unit_scale=True, desc="Ingesting") as pbar:
        last_pos = 0
        for raw_job in ijson.items(f, "item"):
            stats["total_seen"] += 1

            job_id = raw_job.get("job_id")
            if not job_id:
                stats["skipped_no_id"] += 1
                continue
            if job_id in seen_job_ids:
                stats["duplicate_job_id"] += 1
                continue

            record = clean_and_normalize(raw_job)
            fingerprint = record["fingerprint"]
            if fingerprint in seen_fingerprints:
                stats["duplicate_fingerprint"] += 1
                continue

            seen_job_ids.add(job_id)
            seen_fingerprints.add(fingerprint)
            batch.append(record)
            stats["inserted"] += 1

            if len(batch) >= BATCH_SIZE:
                upsert_batch(conn, batch)
                batch = []

            cur_pos = f.tell()
            pbar.update(cur_pos - last_pos)
            last_pos = cur_pos

            if limit and stats["inserted"] >= limit:
                break

    upsert_batch(conn, batch)

    conn.execute("PRAGMA synchronous=NORMAL;")
    rebuild_fts_index(conn)

    stats["preexisting_jobs_in_db_before_run"] = preexisting_job_count
    stats["total_jobs_in_db_after_run"] = preexisting_job_count + stats["inserted"]

    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO ingestion_meta (key, value) VALUES ('last_ingest_stats', ?)",
        (json.dumps(stats),),
    )
    cursor.execute(
        "INSERT OR REPLACE INTO ingestion_meta (key, value) VALUES ('last_ingest_at', ?)",
        (datetime.now(timezone.utc).isoformat(),),
    )
    conn.commit()
    conn.close()
    return stats


def main():
    parser = argparse.ArgumentParser(description="Stream-ingest raw job listings JSON into SQLite.")
    parser.add_argument("input_path", help="Path to the raw jobs JSON array file")
    parser.add_argument("--limit", type=int, default=None, help="Optional cap on number of records inserted")
    args = parser.parse_args()

    stats = ingest(args.input_path, limit=args.limit)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
