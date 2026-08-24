import re

import numpy as np
from fastapi import APIRouter, File, Header, HTTPException, UploadFile
from pydantic import BaseModel

from app.api.jobs import _vector_search_job_ids
from app.db.database import db_session
from app.db.models import row_to_job_dict
from app.services import ai_service, embedding_service
from app.utils.parser import extract_experience_years, extract_resume_text, extract_skills_from_text

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])

MAX_RESUME_VERSIONS = 3


def _skills_jaccard(resume_skills: list, job_skills: list) -> float:
    set_a = {s.lower() for s in resume_skills}
    set_b = {s.lower() for s in job_skills}
    if not set_a and not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    if not union:
        return 0.0
    return len(intersection) / len(union)


def _experience_alignment(resume_years: int, job_min: int, job_max: int) -> float:
    if job_min is None and job_max is None:
        return 0.5
    job_min = job_min if job_min is not None else 0
    job_max = job_max if job_max is not None else job_min + 5
    if job_min <= resume_years <= job_max:
        return 1.0
    distance = min(abs(resume_years - job_min), abs(resume_years - job_max))
    return max(0.0, 1.0 - (distance / 10.0))


def _build_match_explanation(resume_years: int, job: dict, score: dict) -> dict:
    """Deterministic explanation built entirely from already-computed scores - never a
    separate AI guess, so it can never contradict the actual composite score shown."""
    reasons = []

    matched = score["matched_skills"]
    missing = score["missing_skills"]
    total_skills = len(matched) + len(missing)
    if total_skills > 0:
        if not missing:
            reasons.append({"type": "positive", "text": f"All {total_skills}/{total_skills} required skills match."})
        elif len(matched) >= total_skills / 2:
            reasons.append(
                {
                    "type": "positive",
                    "text": f"{len(matched)}/{total_skills} skills match (missing: {', '.join(missing[:4])}).",
                }
            )
        else:
            reasons.append(
                {
                    "type": "warning",
                    "text": f"Only {len(matched)}/{total_skills} skills match (missing: {', '.join(missing[:4])}).",
                }
            )

    job_min, job_max = job.get("experience_min"), job.get("experience_max")
    if job_min is None and job_max is None:
        reasons.append({"type": "neutral", "text": "Experience requirement not specified for this role."})
    elif score["experience_score"] >= 90:
        reasons.append(
            {"type": "positive", "text": f"Experience level: strong fit ({job_min}-{job_max} yrs required, you have {resume_years})."}
        )
    elif score["experience_score"] >= 50:
        reasons.append(
            {"type": "neutral", "text": f"Experience level: close ({job_min}-{job_max} yrs required, you have {resume_years})."}
        )
    else:
        reasons.append(
            {"type": "warning", "text": f"Experience gap: {job_min}-{job_max} yrs required, you have {resume_years}."}
        )

    if score["semantic_score"] >= 70:
        reasons.append({"type": "positive", "text": f"{score['semantic_score']}% semantic similarity to your resume."})
    elif score["semantic_score"] >= 40:
        reasons.append({"type": "neutral", "text": f"{score['semantic_score']}% semantic similarity to your resume."})
    else:
        reasons.append({"type": "warning", "text": f"Low semantic overlap ({score['semantic_score']}%) with your resume."})

    return {"composite_score": score["composite_score"], "reasons": reasons}


def _resume_query_text(resume_text: str, resume_skills: list) -> str:
    return f"{' '.join(resume_skills)} {resume_text[:500]}"


def _job_faiss_indices(conn, job_ids: list) -> dict:
    if not job_ids:
        return {}
    cursor = conn.cursor()
    placeholders = ",".join("?" * len(job_ids))
    cursor.execute(f"SELECT job_id, faiss_index FROM vector_mappings WHERE job_id IN ({placeholders})", job_ids)
    return {r["job_id"]: r["faiss_index"] for r in cursor.fetchall()}


def batch_composite_scores(conn, resume_text: str, resume_skills: list, resume_years: int, jobs: list) -> list:
    """Scores many jobs against one resume using precomputed FAISS vectors for the job side,
    so only the resume itself needs a live embedding call."""
    if not jobs:
        return []

    resume_vec = embedding_service.embed_text(_resume_query_text(resume_text, resume_skills))[0]
    resume_norm = np.linalg.norm(resume_vec)

    job_ids = [job["job_id"] for job in jobs]
    faiss_index_map = _job_faiss_indices(conn, job_ids)
    faiss_indices = [faiss_index_map.get(jid, -1) for jid in job_ids]
    valid_positions = [i for i, fidx in enumerate(faiss_indices) if fidx >= 0]

    job_vecs = np.zeros((len(jobs), embedding_service.EMBEDDING_DIM), dtype=np.float32)
    if valid_positions:
        reconstructed = embedding_service.reconstruct_vectors([faiss_indices[i] for i in valid_positions])
        for pos, vec in zip(valid_positions, reconstructed):
            job_vecs[pos] = vec

    job_norms = np.linalg.norm(job_vecs, axis=1)
    denom = resume_norm * job_norms
    denom[denom == 0] = 1e-9
    semantic_scores = np.clip((job_vecs @ resume_vec) / denom, 0.0, None)

    resume_skill_set = {s.lower() for s in resume_skills}
    results = []
    for job, semantic_score in zip(jobs, semantic_scores):
        skills_score = _skills_jaccard(resume_skills, job["skills"])
        experience_score = _experience_alignment(resume_years, job["experience_min"], job["experience_max"])
        composite = (0.4 * float(semantic_score)) + (0.4 * skills_score) + (0.2 * experience_score)

        score = {
            "composite_score": round(composite * 100, 1),
            "semantic_score": round(float(semantic_score) * 100, 1),
            "skills_score": round(skills_score * 100, 1),
            "experience_score": round(experience_score * 100, 1),
            "matched_skills": [s for s in job["skills"] if s.lower() in resume_skill_set],
            "missing_skills": [s for s in job["skills"] if s.lower() not in resume_skill_set],
        }
        score["match_explanation"] = _build_match_explanation(resume_years, job, score)
        results.append(score)
    return results


@router.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    file_bytes = await file.read()
    max_size = 10 * 1024 * 1024
    if len(file_bytes) > max_size:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    try:
        text = extract_resume_text(file.filename, file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    skills = extract_skills_from_text(text)
    experience_years = extract_experience_years(text)

    return {
        "filename": file.filename,
        "text": text,
        "skills": skills,
        "experience_years": experience_years,
    }


class PersonalizedAnalyticsRequest(BaseModel):
    resume_text: str
    resume_skills: list = []
    experience_years: int = 0
    top_k: int = 250
    min_score: float = 40.0


def _compute_salary_percentiles(pairs: list) -> dict:
    """Same percentile method as the global analytics endpoint, but over an arbitrary
    list of (salary_min, salary_max) pairs instead of a fresh SQL query."""
    if not pairs:
        return {"p25": None, "p50": None, "p75": None, "p90": None, "sample_size": 0}
    midpoints = sorted((smin + smax) / 2 for smin, smax in pairs)
    n = len(midpoints)

    def percentile(p):
        idx = int(round((p / 100) * (n - 1)))
        return round(midpoints[idx], 2)

    return {"p25": percentile(25), "p50": percentile(50), "p75": percentile(75), "p90": percentile(90), "sample_size": n}


@router.post("/personalized-analytics")
def personalized_analytics(request: PersonalizedAnalyticsRequest):
    """Aggregates market analytics over the jobs that actually match this resume, reusing
    the same composite scoring as /match rather than a separate SQL-level filter, so the
    numbers here are consistent with what the user sees in their match list."""
    from app.services.learning_resources import get_learning_link

    with db_session() as conn:
        # Pre-filter via the same FAISS vector search hybrid search already uses, instead
        # of scoring an arbitrary "first 2000 rows" DB slice - this both cuts the scoring
        # workload and ensures the candidates are actually semantically relevant to begin
        # with, rather than whatever order SQLite happens to return.
        query_text = _resume_query_text(request.resume_text, request.resume_skills)
        vector_ids = _vector_search_job_ids(conn, query_text, limit=500)
        if vector_ids:
            cursor = conn.cursor()
            placeholders = ",".join("?" * len(vector_ids))
            cursor.execute(f"SELECT * FROM jobs WHERE job_id IN ({placeholders})", vector_ids)
            rows = cursor.fetchall()
        else:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs LIMIT 500")
            rows = cursor.fetchall()
        jobs = [row_to_job_dict(r) for r in rows]

        scores = batch_composite_scores(conn, request.resume_text, request.resume_skills, request.experience_years, jobs)
        scored_jobs = [{**job, **score} for job, score in zip(jobs, scores)]
        scored_jobs.sort(key=lambda x: x["composite_score"], reverse=True)

        matched = [j for j in scored_jobs if j["composite_score"] >= request.min_score][: request.top_k]

    if not matched:
        return {
            "matched_count": 0,
            "top_companies": [],
            "top_locations": [],
            "top_domains": [],
            "salary_percentiles": {"p25": None, "p50": None, "p75": None, "p90": None, "sample_size": 0},
            "top_skills": [],
            "average_match_score": 0.0,
        }

    def _count_by(key):
        counts = {}
        for j in matched:
            val = j.get(key)
            if val:
                counts[val] = counts.get(val, 0) + 1
        return sorted(({"value": k, "count": v} for k, v in counts.items()), key=lambda x: x["count"], reverse=True)

    top_companies = [{"company_name": c["value"], "count": c["count"]} for c in _count_by("company_name")[:15]]
    top_locations = [{"location": c["value"], "count": c["count"]} for c in _count_by("location")[:15]]
    top_domains = [{"domain": c["value"], "count": c["count"]} for c in _count_by("domain")[:15]]

    salary_pairs = [
        (j["salary_min"], j["salary_max"]) for j in matched if j.get("salary_min") is not None and j.get("salary_max") is not None
    ]
    salary_percentiles = _compute_salary_percentiles(salary_pairs)

    skill_counts = {}
    for j in matched:
        for skill in j.get("skills", []):
            skill_counts[skill] = skill_counts.get(skill, 0) + 1
    top_skills_sorted = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:20]
    top_skills = [{"skill": s, "count": c, "study_link": get_learning_link(s)} for s, c in top_skills_sorted]

    avg_score = round(sum(j["composite_score"] for j in matched) / len(matched), 1)

    return {
        "matched_count": len(matched),
        "average_match_score": avg_score,
        "top_companies": top_companies,
        "top_locations": top_locations,
        "top_domains": top_domains,
        "salary_percentiles": salary_percentiles,
        "top_skills": top_skills,
    }


class MatchRequest(BaseModel):
    resume_text: str
    resume_skills: list = []
    experience_years: int = 0
    top_k: int = 20
    location: str = None
    domain: str = None


@router.post("/match")
def match_jobs(request: MatchRequest):
    with db_session() as conn:
        cursor = conn.cursor()
        clauses = []
        params = []
        if request.location:
            clauses.append("location LIKE ?")
            params.append(f"%{request.location}%")
        if request.domain:
            clauses.append("domain LIKE ?")
            params.append(f"%{request.domain}%")
        where_clause = " AND ".join(clauses) if clauses else "1=1"
        cursor.execute(f"SELECT * FROM jobs WHERE {where_clause} LIMIT 500", params)
        rows = cursor.fetchall()

        jobs = [row_to_job_dict(r) for r in rows]
        scores = batch_composite_scores(conn, request.resume_text, request.resume_skills, request.experience_years, jobs)
        results = [{**job, **score} for job, score in zip(jobs, scores)]

        results.sort(key=lambda x: x["composite_score"], reverse=True)
        return {"matches": results[: request.top_k]}


class SkillsGapRequest(BaseModel):
    resume_skills: list = []
    target_role: str = None
    location: str = None
    limit: int = 300


@router.post("/skills-gap")
def skills_gap(request: SkillsGapRequest):
    """Personalized skills-gap analysis: aggregates skill demand across jobs matching the
    user's target role/location, and flags which of those in-demand skills the resume
    already covers versus which are worth learning, with a curated study link for each."""
    from app.services.learning_resources import get_learning_link

    with db_session() as conn:
        cursor = conn.cursor()
        clauses = []
        params = []
        if request.target_role:
            clauses.append("(title LIKE ? OR skills LIKE ?)")
            params.extend([f"%{request.target_role}%", f"%{request.target_role}%"])
        if request.location:
            clauses.append("location LIKE ?")
            params.append(f"%{request.location}%")
        where_clause = " AND ".join(clauses) if clauses else "1=1"
        cursor.execute(f"SELECT skills FROM jobs WHERE {where_clause} AND skills != '' LIMIT ?", params + [request.limit])
        rows = cursor.fetchall()

    if not rows:
        return {"matched_jobs": 0, "have": [], "gap": []}

    demand_counts = {}
    display_casing = {}
    for row in rows:
        for skill in row["skills"].split(","):
            skill = skill.strip()
            if not skill:
                continue
            key = skill.lower()
            demand_counts[key] = demand_counts.get(key, 0) + 1
            display_casing.setdefault(key, skill)

    resume_skill_set = {s.lower() for s in request.resume_skills}
    have = []
    gap = []
    for key, count in demand_counts.items():
        entry = {
            "skill": display_casing[key],
            "demand_count": count,
            "demand_pct": round(count / len(rows) * 100, 1),
        }
        if key in resume_skill_set:
            have.append(entry)
        else:
            entry["study_link"] = get_learning_link(display_casing[key])
            gap.append(entry)

    have.sort(key=lambda x: x["demand_count"], reverse=True)
    gap.sort(key=lambda x: x["demand_count"], reverse=True)

    return {"matched_jobs": len(rows), "have": have[:20], "gap": gap[:20]}


class ATSAnalyzeRequest(BaseModel):
    resume_text: str
    job_id: str


@router.post("/ats-analyze")
def ats_analyze(request: ATSAnalyzeRequest, x_gemini_api_key: str = Header(None)):
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (request.job_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Job not found")
        job = row_to_job_dict(row)

    analysis = ai_service.analyze_ats_match(request.resume_text, job, api_key=x_gemini_api_key)
    return analysis


class OptimizeRequest(BaseModel):
    resume_text: str
    job_id: str


@router.post("/optimize-phrasing")
def optimize_phrasing(request: OptimizeRequest, x_gemini_api_key: str = Header(None)):
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (request.job_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Job not found")
        job = row_to_job_dict(row)

    suggestions = ai_service.optimize_resume_phrasing(request.resume_text, job, api_key=x_gemini_api_key)
    return {"suggestions": suggestions}


def _single_job_score(conn, resume_text: str, resume_skills: list, experience_years: int, job: dict) -> dict:
    scores = batch_composite_scores(conn, resume_text, resume_skills, experience_years, [job])
    return scores[0]


def _build_skill_highlights(resume_text: str, job_skills: list) -> list:
    """Returns spans marking where each job skill is (or isn't) found in the resume,
    for inline highlighting in the UI. Never claims a skill is present when it isn't.
    Uses word-boundary matching so short skill names (R, C, Go) don't false-positive
    on substrings inside unrelated words."""
    highlights = []
    for skill in job_skills:
        pattern = r"(?<![a-zA-Z0-9])" + re.escape(skill) + r"(?![a-zA-Z0-9])"
        match = re.search(pattern, resume_text, re.IGNORECASE)
        highlights.append(
            {
                "skill": skill,
                "matched": match is not None,
                "position": match.start() if match else None,
            }
        )
    return highlights


class FitScoreRequest(BaseModel):
    resume_text: str
    resume_skills: list = []
    experience_years: int = 0
    job_id: str


@router.post("/fit-score")
def fit_score(request: FitScoreRequest):
    """Lightweight single-job scoring endpoint - same composite score and deterministic
    explanation as /match, but for one specific job a user is already looking at, without
    the overhead of scanning up to 500 jobs like /match does."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (request.job_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Job not found")
        job = row_to_job_dict(row)

        score = _single_job_score(conn, request.resume_text, request.resume_skills, request.experience_years, job)

    return score


class BoostResumeRequest(BaseModel):
    resume_text: str
    resume_skills: list = []
    experience_years: int = 0
    job_id: str


@router.post("/boost-resume")
def boost_resume(request: BoostResumeRequest, x_gemini_api_key: str = Header(None)):
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (request.job_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Job not found")
        job = row_to_job_dict(row)

        original_score = _single_job_score(conn, request.resume_text, request.resume_skills, request.experience_years, job)

        boost_result = ai_service.boost_resume_presentation(request.resume_text, job, api_key=x_gemini_api_key)
        rewrites = boost_result.get("rewrites", [])

        rewritten_text = ai_service.apply_resume_rewrites(request.resume_text, rewrites)
        boosted_score = _single_job_score(conn, rewritten_text, request.resume_skills, request.experience_years, job)

        highlights = _build_skill_highlights(request.resume_text, job["skills"])

    return {
        "original_score": original_score["composite_score"],
        "boosted_score": boosted_score["composite_score"],
        "boost_delta": round(boosted_score["composite_score"] - original_score["composite_score"], 1),
        "rewrites": rewrites,
        "skill_highlights": highlights,
        "matched_skills": original_score["matched_skills"],
        "missing_skills": original_score["missing_skills"],
        "source": boost_result.get("source", "heuristic"),
    }


class CoverLetterRequest(BaseModel):
    resume_text: str
    resume_skills: list = []
    experience_years: int = 0
    job_id: str


@router.post("/cover-letter")
def cover_letter(request: CoverLetterRequest, x_gemini_api_key: str = Header(None)):
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (request.job_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Job not found")
        job = row_to_job_dict(row)

        score = _single_job_score(conn, request.resume_text, request.resume_skills, request.experience_years, job)

    result = ai_service.generate_cover_letter(
        request.resume_text, job, score["matched_skills"], api_key=x_gemini_api_key
    )

    return {
        "letter": result["letter"],
        "source": result["source"],
        "job_title": job["title"],
        "company_name": job["company_name"],
    }


class CompareResumesRequest(BaseModel):
    resumes: list
    target_role: str = None
    location: str = None
    job_id: str = None
    mode: str = "recommend"


@router.post("/compare-resumes")
def compare_resumes(request: CompareResumesRequest, x_gemini_api_key: str = Header(None)):
    if len(request.resumes) < 1 or len(request.resumes) > MAX_RESUME_VERSIONS:
        raise HTTPException(status_code=400, detail=f"Provide between 1 and {MAX_RESUME_VERSIONS} resume versions")
    if request.mode not in ("recommend", "generate"):
        raise HTTPException(status_code=400, detail="mode must be 'recommend' or 'generate'")

    target_job = None
    with db_session() as conn:
        cursor = conn.cursor()

        if request.job_id:
            cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (request.job_id,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Job not found")
            target_job = row_to_job_dict(row)
            jobs = [target_job]
        else:
            clauses = []
            params = []
            if request.target_role:
                clauses.append("(title LIKE ? OR skills LIKE ?)")
                params.extend([f"%{request.target_role}%", f"%{request.target_role}%"])
            if request.location:
                clauses.append("location LIKE ?")
                params.append(f"%{request.location}%")
            where_clause = " AND ".join(clauses) if clauses else "1=1"
            cursor.execute(f"SELECT * FROM jobs WHERE {where_clause} LIMIT 300", params)
            rows = cursor.fetchall()
            jobs = [row_to_job_dict(r) for r in rows]

        comparison = []
        for i, resume in enumerate(request.resumes):
            resume_text = resume.get("text", "")
            resume_skills = resume.get("skills", [])
            experience_years = resume.get("experience_years", 0)
            label = resume.get("label", f"Resume {i + 1}")

            scores = batch_composite_scores(conn, resume_text, resume_skills, experience_years, jobs)
            scored_jobs = [{**job, **score} for job, score in zip(jobs, scores)]
            scored_jobs.sort(key=lambda x: x["composite_score"], reverse=True)
            top_matches = scored_jobs[:10]
            avg_score = round(sum(j["composite_score"] for j in top_matches) / len(top_matches), 1) if top_matches else 0.0

            comparison.append(
                {
                    "label": label,
                    "average_top_match_score": avg_score,
                    "top_matches": top_matches,
                    "skills_detected": resume_skills,
                    "experience_years": experience_years,
                    "_text": resume_text,
                }
            )

    comparison.sort(key=lambda x: x["average_top_match_score"], reverse=True)

    recommendation = None
    if request.mode == "recommend":
        scored_for_pick = [
            {"label": c["label"], "score": c["average_top_match_score"], "experience_years": c["experience_years"]}
            for c in comparison
        ]
        recommendation = ai_service.recommend_best_resume(scored_for_pick)
    elif request.mode == "generate":
        merge_input = [{"label": c["label"], "text": c["_text"]} for c in comparison]
        merge_result = ai_service.generate_merged_resume(merge_input, job=target_job, api_key=x_gemini_api_key)
        if merge_result["merged_text"] is None:
            # Grounding failed or no Gemini key - fall back to the recommend mode instead of
            # silently returning nothing, so the caller always gets a usable answer.
            scored_for_pick = [
                {"label": c["label"], "score": c["average_top_match_score"], "experience_years": c["experience_years"]}
                for c in comparison
            ]
            recommendation = ai_service.recommend_best_resume(scored_for_pick)
        else:
            recommendation = {"merged_text": merge_result["merged_text"], "source": merge_result["source"]}

    for c in comparison:
        del c["_text"]

    return {"comparison": comparison, "mode": request.mode, "recommendation": recommendation}
