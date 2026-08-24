"""NDCG@10, MRR retrieval quality metrics, and RAG faithfulness self-audit."""
import math

from app.db.database import db_session

PROBE_QUERIES = [
    {"query": "python data scientist", "relevant_terms": ["python", "data scientist", "machine learning"]},
    {"query": "react frontend developer", "relevant_terms": ["react", "frontend", "javascript"]},
    {"query": "java backend engineer", "relevant_terms": ["java", "backend", "spring"]},
    {"query": "product manager remote", "relevant_terms": ["product manager", "product"]},
    {"query": "devops kubernetes aws", "relevant_terms": ["devops", "kubernetes", "aws"]},
    {"query": "sql data analyst", "relevant_terms": ["sql", "data analyst", "analytics"]},
]


def _relevance_label(job: dict, relevant_terms: list) -> int:
    haystack = f"{job.get('title', '')} {job.get('description', '')} {' '.join(job.get('skills', []))}".lower()
    hits = sum(1 for term in relevant_terms if term.lower() in haystack)
    if hits >= 2:
        return 2
    if hits == 1:
        return 1
    return 0


def _dcg(relevances: list) -> float:
    return sum(rel / math.log2(idx + 2) for idx, rel in enumerate(relevances))


def _ndcg_at_k(relevances: list, k: int = 10) -> float:
    relevances = relevances[:k]
    dcg = _dcg(relevances)
    ideal = _dcg(sorted(relevances, reverse=True))
    if ideal == 0:
        return 0.0
    return dcg / ideal


def _mrr_single(relevances: list) -> float:
    for idx, rel in enumerate(relevances):
        if rel > 0:
            return 1.0 / (idx + 1)
    return 0.0


def run_evaluation() -> dict:
    from app.api.jobs import hybrid_search

    ndcg_scores = []
    mrr_scores = []
    per_query = []

    with db_session() as conn:
        for probe in PROBE_QUERIES:
            job_ids = hybrid_search(conn, probe["query"], limit=10)
            if not job_ids:
                ndcg_scores.append(0.0)
                mrr_scores.append(0.0)
                per_query.append({"query": probe["query"], "ndcg": 0.0, "mrr": 0.0, "results_found": 0})
                continue

            cursor = conn.cursor()
            placeholders = ",".join("?" * len(job_ids))
            cursor.execute(f"SELECT * FROM jobs WHERE job_id IN ({placeholders})", job_ids)
            rows = {r["job_id"]: dict(r) for r in cursor.fetchall()}

            relevances = []
            for job_id in job_ids:
                row = rows.get(job_id)
                if not row:
                    relevances.append(0)
                    continue
                skills = [s.strip() for s in (row["skills"] or "").split(",") if s.strip()]
                job_dict = {"title": row["title"], "description": row["description"], "skills": skills}
                relevances.append(_relevance_label(job_dict, probe["relevant_terms"]))

            ndcg = _ndcg_at_k(relevances, k=10)
            mrr = _mrr_single(relevances)
            ndcg_scores.append(ndcg)
            mrr_scores.append(mrr)
            per_query.append({"query": probe["query"], "ndcg": round(ndcg, 3), "mrr": round(mrr, 3), "results_found": len(job_ids)})

    avg_ndcg = round(sum(ndcg_scores) / len(ndcg_scores), 3) if ndcg_scores else 0.0
    avg_mrr = round(sum(mrr_scores) / len(mrr_scores), 3) if mrr_scores else 0.0

    return {
        "ndcg_at_10": avg_ndcg,
        "mrr": avg_mrr,
        "per_query": per_query,
        "faithfulness_audit": run_faithfulness_audit(),
    }


def run_faithfulness_audit() -> dict:
    """Checks that heuristic/Gemini chat responses stay grounded in supplied job context
    by verifying no hallucinated numeric claims appear in a sample of heuristic responses."""
    from app.services import ai_service

    sample_job = {
        "title": "Backend Engineer",
        "company_name": "Acme Corp",
        "salary_min": None,
        "salary_max": None,
        "skills": ["Python", "FastAPI"],
    }
    response = ai_service.career_chat_heuristic("what is the salary?", {"job": sample_job, "history": []})
    no_hallucinated_number = not any(char.isdigit() for char in response)

    return {
        "test_name": "salary_hallucination_check",
        "passed": no_hallucinated_number,
        "detail": "Heuristic chat correctly avoids inventing a salary figure when none is present in job data."
        if no_hallucinated_number
        else "Heuristic chat may have hallucinated a numeric salary not present in source data.",
    }
