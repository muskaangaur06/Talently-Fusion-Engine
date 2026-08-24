import math
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.db.database import db_session
from app.db.models import row_to_job_dict
from app.services import embedding_service
from app.services.ai_service import LOCATION_ALIASES

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

RRF_K = 60


def _fts_search(conn, query: str, limit: int = 100):
    if not query.strip():
        return []
    cursor = conn.cursor()
    fts_query = " OR ".join(f'"{tok}"' for tok in query.split() if tok)
    if not fts_query:
        return []
    try:
        cursor.execute(
            """
            SELECT job_id, bm25(jobs_fts) as rank_score
            FROM jobs_fts
            WHERE jobs_fts MATCH ?
            ORDER BY rank_score
            LIMIT ?
            """,
            (fts_query, limit),
        )
        rows = cursor.fetchall()
        return [r["job_id"] for r in rows]
    except Exception:
        return []


def _vector_search_job_ids(conn, query: str, limit: int = 100):
    results = embedding_service.vector_search(query, top_k=limit)
    if not results:
        return []
    faiss_indices = [r[0] for r in results]
    cursor = conn.cursor()
    placeholders = ",".join("?" * len(faiss_indices))
    cursor.execute(
        f"SELECT faiss_index, job_id FROM vector_mappings WHERE faiss_index IN ({placeholders})",
        faiss_indices,
    )
    idx_to_job = {r["faiss_index"]: r["job_id"] for r in cursor.fetchall()}
    ordered_ids = []
    for faiss_idx, _dist in results:
        job_id = idx_to_job.get(faiss_idx)
        if job_id:
            ordered_ids.append(job_id)
    return ordered_ids


def reciprocal_rank_fusion(rank_lists: list, k: int = RRF_K) -> list:
    scores = {}
    for rank_list in rank_lists:
        for rank, job_id in enumerate(rank_list):
            scores[job_id] = scores.get(job_id, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def hybrid_search(conn, query: str, limit: int = 100) -> list:
    fts_ids = _fts_search(conn, query, limit=limit)
    vector_ids = _vector_search_job_ids(conn, query, limit=limit)
    if not fts_ids and not vector_ids:
        return []
    fused = reciprocal_rank_fusion([fts_ids, vector_ids])
    return [job_id for job_id, _score in fused[:limit]]


class JobListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    jobs: list


@router.get("", response_model=JobListResponse)
def list_jobs(
    q: str = Query("", description="Free-text search query"),
    location: str = Query(None),
    source: str = Query(None),
    min_experience: int = Query(None),
    max_experience: int = Query(None),
    domain: str = Query(None),
    max_age_days: int = Query(None, description="Only jobs posted within this many days"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    with db_session() as conn:
        if q.strip():
            candidate_ids = hybrid_search(conn, q, limit=500)
            if not candidate_ids:
                return JobListResponse(total=0, page=page, page_size=page_size, total_pages=0, jobs=[])
            order_map = {job_id: i for i, job_id in enumerate(candidate_ids)}
            placeholders = ",".join("?" * len(candidate_ids))
            filter_clauses, filter_params = _build_filters(location, source, min_experience, max_experience, domain, max_age_days)
            where_clause = f"job_id IN ({placeholders})"
            if filter_clauses:
                where_clause += " AND " + " AND ".join(filter_clauses)
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM jobs WHERE {where_clause}", candidate_ids + filter_params)
            rows = cursor.fetchall()
            rows = sorted(rows, key=lambda r: order_map.get(r["job_id"], math.inf))
            total = len(rows)
            start = (page - 1) * page_size
            page_rows = rows[start:start + page_size]
        else:
            filter_clauses, filter_params = _build_filters(location, source, min_experience, max_experience, domain, max_age_days)
            where_clause = " AND ".join(filter_clauses) if filter_clauses else "1=1"
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) as c FROM jobs WHERE {where_clause}", filter_params)
            total = cursor.fetchone()["c"]
            offset = (page - 1) * page_size
            cursor.execute(
                f"SELECT * FROM jobs WHERE {where_clause} ORDER BY posted_at DESC LIMIT ? OFFSET ?",
                filter_params + [page_size, offset],
            )
            page_rows = cursor.fetchall()

        jobs = [row_to_job_dict(r) for r in page_rows]
        total_pages = math.ceil(total / page_size) if page_size else 0
        return JobListResponse(total=total, page=page, page_size=page_size, total_pages=total_pages, jobs=jobs)


def _build_filters(location, source, min_experience, max_experience, domain, max_age_days=None):
    clauses = []
    params = []
    if location:
        normalized_location = LOCATION_ALIASES.get(location.strip().lower(), location)
        clauses.append("location LIKE ?")
        params.append(f"%{normalized_location}%")
    if source:
        clauses.append("source = ?")
        params.append(source)
    if domain:
        clauses.append("domain LIKE ?")
        params.append(f"%{domain}%")
    if min_experience is not None:
        clauses.append("(experience_max IS NULL OR experience_max >= ?)")
        params.append(min_experience)
    if max_experience is not None:
        clauses.append("(experience_min IS NULL OR experience_min <= ?)")
        params.append(max_experience)
    if max_age_days is not None:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=max_age_days)).isoformat()
        clauses.append("posted_at >= ?")
        params.append(cutoff)
    return clauses, params


@router.get("/{job_id}")
def get_job(job_id: str):
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
        row = cursor.fetchone()
        if not row:
            return {"error": "Job not found"}
        return row_to_job_dict(row)


@router.get("/{job_id}/similar")
def get_similar_jobs(job_id: str, limit: int = Query(6, ge=1, le=20)):
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
        row = cursor.fetchone()
        if not row:
            return {"error": "Job not found"}
        job = row_to_job_dict(row)
        query_text = f"{job['title']} {' '.join(job['skills'])} {job['domain']}"
        similar_ids = _vector_search_job_ids(conn, query_text, limit=limit + 1)
        similar_ids = [jid for jid in similar_ids if jid != job_id][:limit]
        if not similar_ids:
            return {"jobs": []}
        placeholders = ",".join("?" * len(similar_ids))
        cursor.execute(f"SELECT * FROM jobs WHERE job_id IN ({placeholders})", similar_ids)
        rows = {r["job_id"]: row_to_job_dict(r) for r in cursor.fetchall()}
        return {"jobs": [rows[jid] for jid in similar_ids if jid in rows]}
