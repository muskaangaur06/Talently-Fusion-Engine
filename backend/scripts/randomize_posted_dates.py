"""One-time data-quality fix for the dummy/demo dataset: the ingested posted_at values
are all timestamped from the same source-scrape window and don't reflect real-world
posting recency, so every job looked equally "fresh" and a job-age filter would be
meaningless. This rewrites posted_at to a realistic spread from today back to 6 months
ago, weighted toward more recent dates (real job boards skew recent - most listings are
under a month old, a shrinking tail goes back further), and standardizes the format to
ISO 8601 so it sorts and filters correctly in SQLite (the original "YYYY/M/D, HH:MM"
text format does not sort chronologically as a string).

Safe to re-run - it always overwrites posted_at for every row with a fresh random draw.
"""
import os
import random
import sys
from datetime import datetime, timedelta, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import get_connection  # noqa: E402

MAX_AGE_DAYS = 180


def weighted_age_days() -> int:
    """Skews toward recent postings: roughly half within the first month, a shrinking
    tail out to 6 months, via an exponential-ish draw rather than a flat distribution."""
    u = random.random()
    # u**2.2 concentrates draws toward 0 (recent) while still reaching the full range.
    return int((u ** 2.2) * MAX_AGE_DAYS)


def main():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT job_id FROM jobs")
    job_ids = [r["job_id"] for r in cursor.fetchall()]

    now = datetime.now(timezone.utc)
    updates = []
    for job_id in job_ids:
        age_days = weighted_age_days()
        age_seconds = random.randint(0, 86400)
        posted = now - timedelta(days=age_days, seconds=age_seconds)
        updates.append((posted.isoformat(), job_id))

    cursor.executemany("UPDATE jobs SET posted_at = ? WHERE job_id = ?", updates)
    conn.commit()

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_posted_at ON jobs(posted_at);")
    conn.commit()
    conn.close()

    print(f"Updated posted_at for {len(updates)} jobs with a realistic 0-{MAX_AGE_DAYS}-day spread.")


if __name__ == "__main__":
    main()
