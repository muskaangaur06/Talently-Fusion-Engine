from fastapi import APIRouter, Header
from pydantic import BaseModel

from app.db.database import db_session
from app.db.models import row_to_job_dict
from app.services import ai_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ParseIntentRequest(BaseModel):
    query: str


@router.post("/parse-intent")
def parse_intent(request: ParseIntentRequest, x_gemini_api_key: str = Header(None)):
    filters = ai_service.parse_query_intent(request.query, api_key=x_gemini_api_key)
    return filters


class ChatRequest(BaseModel):
    message: str
    job_id: str = None
    history: list = []
    resume_skills: list = []
    experience_years: int = None


@router.post("")
def chat(request: ChatRequest, x_gemini_api_key: str = Header(None)):
    job = None
    if request.job_id:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (request.job_id,))
            row = cursor.fetchone()
            if row:
                job = row_to_job_dict(row)

    context = {
        "job": job,
        "history": request.history,
        "resume_skills": request.resume_skills,
        "experience_years": request.experience_years,
    }
    reply = ai_service.career_chat(request.message, context, api_key=x_gemini_api_key)
    return {"reply": reply}


class InterviewPrepRequest(BaseModel):
    job_id: str
    resume_skills: list = []


@router.post("/interview-prep")
def interview_prep(request: InterviewPrepRequest, x_gemini_api_key: str = Header(None)):
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (request.job_id,))
        row = cursor.fetchone()
        if not row:
            return {"error": "Job not found"}
        job = row_to_job_dict(row)

    matched_skills = missing_skills = None
    if request.resume_skills:
        resume_skill_set = {s.lower() for s in request.resume_skills}
        matched_skills = [s for s in job["skills"] if s.lower() in resume_skill_set]
        missing_skills = [s for s in job["skills"] if s.lower() not in resume_skill_set]

    prep = ai_service.generate_interview_prep(
        job, api_key=x_gemini_api_key, matched_skills=matched_skills, missing_skills=missing_skills
    )
    return prep
