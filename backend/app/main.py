import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api import analytics, chat, jobs, recommendations
from app.db.database import get_connection, init_schema

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="AI-Powered Job Board", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    conn = get_connection()
    init_schema(conn)
    conn.close()


app.include_router(jobs.router)
app.include_router(recommendations.router)
app.include_router(chat.router)
app.include_router(analytics.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
