"""Fuzzy near-duplicate detection: the same real opening is often re-scraped and
re-posted over time under a new job_id, with a title that differs only in punctuation
or minor phrasing (e.g. "Application Developer: Experience Front End" vs
"Application Developer-Experience Front End"). The ingestion pipeline's exact
fingerprint (company|title|location) dedup does not catch these.

This is a deliberately narrow pass, run after ingestion, not during it:

- Only compares jobs within the SAME (company_name, location) bucket. Comparing
  across locations is wrong here - the same role is legitimately posted separately
  per city (verified against the real dataset: e.g. IBM posts "Data Scientist" as
  distinct real openings in Pune, Kochi, Noida, Mumbai, each with its own apply
  link), so cross-location fuzzy matching would incorrectly merge genuinely
  different job openings.

- A raw SequenceMatcher threshold alone is not safe: an earlier pass at 0.85 merged
  "PHP fullstack developer" with ".NET fullstack developer" (different tech stacks)
  and three unrelated internship roles that only shared the boilerplate suffix
  "...internship opportunity". Time gap between postings also does not reliably
  separate true reposts from false merges in this dataset - some genuine reposts
  are 74+ days apart while some false merges are only 10-28 days apart - so it is
  used only as a secondary guard, not the primary signal.

  Two titles are only treated as the same opening reposted over time if ALL of:
  (1) SequenceMatcher similarity >= SIMILARITY_THRESHOLD (raised from 0.85 to 0.92);
  (2) a seniority/level indicator (roman numerals I-V, "Level N", "LN") is treated as
      incompatible whenever it differs between the two titles, INCLUDING when only one
      title has one at all - "Business Analyst II" vs "Business Analyst I" are distinct,
      and so are "Business Analyst" (no level stated) vs "Business Analyst I" (a
      specific level), confirmed in the dataset;
  (3) if the only words differing between the titles look like job-requisition codes
      (mixed letters+digits, e.g. "bfs039843" vs "bfs039339"), reject the match - these
      are near-certainly distinct real openings under different requisition numbers,
      confirmed in the dataset (multiple "Business Analyst bfs0XXXXX" postings, each
      with its own code, at the same company/location);
  (4) any experience-year range stated directly in the title (e.g. "4 to 8 years",
      "3-5 yrs") must match if both titles state one - "Data Science | 6 to 12 years |
      Pan India" vs "...4 to 8 years..." are different postings, confirmed in the dataset;
  (5) the title's leading job-title word (the first significant word, e.g. "business" in
      "Business Analyst", "data" in "Data Scientist") must match - this catches structured
      titles like "Data Scientist II, Analytics Technology and Engineering (ATE)" vs
      "Applied Scientist II, Analytics Technology and Engineering (ATE)", which share
      enough of the trailing team-name text to pass every other check despite being
      different job titles entirely, confirmed in the dataset;
  (6) they share at least one significant word after stripping generic filler terms
      (developer, engineer, analyst, internship, opportunity, years, immediate,
      joiner, etc.) - so "php developer" and ".net developer" no longer match on
      "developer" alone, but "mern stack developer" reposted twice still does.

  Within a surviving group, only the most recently posted_at row is kept.
"""
import argparse
import os
import re
import sys
from datetime import datetime
from difflib import SequenceMatcher

from tqdm import tqdm

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import get_connection  # noqa: E402
from ingest_data import rebuild_fts_index  # noqa: E402

SIMILARITY_THRESHOLD = 0.92
MAX_REPOST_GAP_DAYS = 548  # ~18 months; beyond this, treat as a separate hiring cycle

GENERIC_TITLE_WORDS = {
    "developer", "engineer", "analyst", "architect", "specialist", "consultant",
    "manager", "lead", "senior", "junior", "trainee", "intern", "internship",
    "opportunity", "opportunities", "immediate", "joiner", "joiners", "years",
    "year", "job", "jobs", "position", "role", "full", "stack", "fullstack",
    "and", "or", "for", "the", "a", "an", "at", "of", "in", "to", "with",
}

ROMAN_NUMERAL_LEVELS = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5}


def _parse_posted_at(value: str):
    """posted_at arrives as e.g. '2024/3/2, 23:41'. Falls back to epoch-zero for
    unparseable/empty values so they sort as oldest, never as newest."""
    if not value:
        return datetime.min
    for fmt in ("%Y/%m/%d, %H:%M", "%Y/%m/%d"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return datetime.min


def _normalize_title(title: str) -> str:
    return " ".join(title.lower().replace("-", " ").replace(":", " ").split())


def _significant_words(normalized_title: str) -> set:
    return {w for w in normalized_title.split() if w not in GENERIC_TITLE_WORDS and len(w) > 1}


def _looks_like_requisition_code(word: str) -> bool:
    """Detects job-requisition-style tokens: either a mix of letters and digits
    (e.g. 'bfs039843', 'ins027160') or a long pure-digit ID (e.g. '19542',
    '20240711213203' - the latter is timestamp-shaped). Both are long enough that
    they're very unlikely to be an ordinary word or a small number like an experience
    year count. Two titles that are otherwise identical except for tokens like this
    are almost certainly separate real job openings under different requisition
    numbers, not the same posting reposted - confirmed against the real dataset: five
    "Business Analyst" postings under distinct bfs0XXXXX codes, and a 9-way group of
    "Data Scientist Artificial Intelligence <digits>" postings each with their own
    numeric req ID, all at the same company/location."""
    has_letter = any(c.isalpha() for c in word)
    has_digit = any(c.isdigit() for c in word)
    if has_letter and has_digit and len(word) >= 5:
        return True
    if word.isdigit() and len(word) >= 5:
        return True
    return False


def _extract_seniority_level(normalized_title: str):
    """Finds a seniority/level indicator in a title: a standalone roman numeral
    (I/II/III/IV/V, as in 'Business Analyst II') or a 'level N'/'LN' pattern (as in
    'Data Engineer (Level 5)'). Returns None if no such indicator is present, so titles
    with no level marker at all are not penalized. Confirmed against the real dataset:
    "Business Analyst II" and "Business Analyst I" are distinct real postings, as are
    "Data Engineer (Level 5)" and "(Level 4)" - these must never be treated as reposts
    of each other."""
    words = normalized_title.split()
    for word in words:
        clean = word.strip("(),.")
        if clean in ROMAN_NUMERAL_LEVELS:
            return ROMAN_NUMERAL_LEVELS[clean]

    match = re.search(r"\blevel\s*(\d+)\b", normalized_title)
    if match:
        return int(match.group(1))
    match = re.search(r"\bl(\d+)\b", normalized_title)
    if match:
        return int(match.group(1))
    return None


def _extract_experience_range(normalized_title: str):
    """Finds an explicit experience-year range stated in the title itself, e.g.
    '4 to 8 years' or '3-5 yrs'. Returns None if no such range is present, so titles
    with no stated range at all are not penalized. Confirmed in the dataset:
    "Data Science | 6 to 12 years | Pan India" vs "...4 to 8 years..." are different
    real postings for different experience bands, not reposts of each other."""
    match = re.search(r"\b(\d+)\s*(?:to|-)\s*(\d+)\s*(?:years|yrs|year)\b", normalized_title)
    if match:
        return (int(match.group(1)), int(match.group(2)))
    return None


def _leading_title_word(normalized_title: str):
    """The first significant word in a title is usually the head of the job title
    itself (e.g. 'data' in 'Data Scientist', 'business' in 'Business Analyst').
    Requiring this to match catches structured titles that share enough trailing
    team-name text to pass every other check while being different job titles -
    confirmed in the dataset: "Data Scientist II, Analytics Technology and
    Engineering (ATE)" vs "Applied Scientist II, Analytics Technology and
    Engineering (ATE)" differ only in this leading word."""
    words = [w for w in normalized_title.split() if w not in GENERIC_TITLE_WORDS and len(w) > 1]
    return words[0] if words else None


def _is_same_opening(title_a: str, title_b: str) -> bool:
    similarity = SequenceMatcher(None, title_a, title_b).ratio()
    if similarity < SIMILARITY_THRESHOLD:
        return False

    level_a = _extract_seniority_level(title_a)
    level_b = _extract_seniority_level(title_b)
    if level_a != level_b:
        return False

    exp_a = _extract_experience_range(title_a)
    exp_b = _extract_experience_range(title_b)
    if exp_a is not None and exp_b is not None and exp_a != exp_b:
        return False

    head_a = _leading_title_word(title_a)
    head_b = _leading_title_word(title_b)
    if head_a is not None and head_b is not None and head_a != head_b:
        return False

    words_a = _significant_words(title_a)
    words_b = _significant_words(title_b)

    only_in_a = words_a - words_b
    only_in_b = words_b - words_a
    differing_words = only_in_a | only_in_b
    if differing_words and all(_looks_like_requisition_code(w) for w in differing_words):
        return False

    if not words_a or not words_b:
        return True
    return bool(words_a & words_b)


def find_near_duplicate_groups(conn):
    """Yields lists of (job_id, normalized_title, posted_at) that are near-duplicates
    of each other, scoped per (company_name, location) bucket."""
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT company_name, location FROM jobs WHERE company_name != ''")
    bucket_keys = cursor.fetchall()

    for bucket in tqdm(bucket_keys, desc="Scanning company+location buckets"):
        cursor.execute(
            "SELECT job_id, title, posted_at FROM jobs WHERE company_name = ? AND location = ?",
            (bucket["company_name"], bucket["location"]),
        )
        jobs_in_bucket = cursor.fetchall()
        if len(jobs_in_bucket) < 2:
            continue

        normalized = [(r["job_id"], _normalize_title(r["title"]), r["posted_at"]) for r in jobs_in_bucket]
        visited = set()

        for i in range(len(normalized)):
            if normalized[i][0] in visited:
                continue
            group = [normalized[i]]
            visited.add(normalized[i][0])
            for j in range(i + 1, len(normalized)):
                if normalized[j][0] in visited:
                    continue
                if not _is_same_opening(normalized[i][1], normalized[j][1]):
                    continue
                gap_days = abs((_parse_posted_at(normalized[i][2]) - _parse_posted_at(normalized[j][2])).days)
                if gap_days > MAX_REPOST_GAP_DAYS:
                    continue
                group.append(normalized[j])
                visited.add(normalized[j][0])
            if len(group) > 1:
                yield group


def dedupe_near_duplicates(dry_run: bool = False) -> dict:
    conn = get_connection()

    stats = {"groups_found": 0, "jobs_removed": 0}
    to_delete = []

    for group in find_near_duplicate_groups(conn):
        stats["groups_found"] += 1
        group_sorted = sorted(group, key=lambda g: _parse_posted_at(g[2]), reverse=True)
        remove = group_sorted[1:]
        to_delete.extend(jid for jid, _title, _posted in remove)
        stats["jobs_removed"] += len(remove)

    if not dry_run and to_delete:
        cursor = conn.cursor()
        placeholders = ",".join("?" * len(to_delete))
        cursor.execute(f"DELETE FROM vector_mappings WHERE job_id IN ({placeholders})", to_delete)
        cursor.execute(f"DELETE FROM jobs WHERE job_id IN ({placeholders})", to_delete)
        conn.commit()
        rebuild_fts_index(conn)

    conn.close()
    return stats


def main():
    parser = argparse.ArgumentParser(description="Remove fuzzy near-duplicate job postings (same company+location).")
    parser.add_argument("--dry-run", action="store_true", help="Report what would be removed without deleting")
    args = parser.parse_args()

    stats = dedupe_near_duplicates(dry_run=args.dry_run)
    print(stats)


if __name__ == "__main__":
    main()
