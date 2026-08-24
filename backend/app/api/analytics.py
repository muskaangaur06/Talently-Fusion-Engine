from fastapi import APIRouter

from app.db.database import db_session
from app.services.evaluation_service import run_evaluation
from app.services.learning_resources import get_learning_link

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("")
def get_analytics():
    with db_session() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as c FROM jobs")
        total_jobs = cursor.fetchone()["c"]

        cursor.execute("SELECT source, COUNT(*) as c FROM jobs GROUP BY source ORDER BY c DESC")
        sources = [{"source": r["source"], "count": r["c"]} for r in cursor.fetchall()]

        cursor.execute("SELECT location, COUNT(*) as c FROM jobs GROUP BY location ORDER BY c DESC LIMIT 15")
        top_locations = [{"location": r["location"], "count": r["c"]} for r in cursor.fetchall()]

        cursor.execute("SELECT domain, COUNT(*) as c FROM jobs WHERE domain != '' GROUP BY domain ORDER BY c DESC LIMIT 15")
        top_domains = [{"domain": r["domain"], "count": r["c"]} for r in cursor.fetchall()]

        cursor.execute(
            "SELECT salary_min, salary_max FROM jobs WHERE salary_min IS NOT NULL AND salary_max IS NOT NULL"
        )
        salary_rows = cursor.fetchall()
        salary_percentiles = _compute_salary_percentiles(salary_rows)

        cursor.execute(
            """
            SELECT
                CASE
                    WHEN experience_min IS NULL THEN 'Not specified'
                    WHEN experience_min = 0 THEN 'Entry level (0-1 yrs)'
                    WHEN experience_min BETWEEN 1 AND 3 THEN 'Junior (1-3 yrs)'
                    WHEN experience_min BETWEEN 4 AND 7 THEN 'Mid (4-7 yrs)'
                    ELSE 'Senior (8+ yrs)'
                END as bucket,
                COUNT(*) as c
            FROM jobs
            GROUP BY bucket
            """
        )
        experience_distribution = [{"bucket": r["bucket"], "count": r["c"]} for r in cursor.fetchall()]

        cursor.execute("SELECT skills FROM jobs WHERE skills != ''")
        skill_counts = {}
        for row in cursor.fetchall():
            for skill in row["skills"].split(","):
                skill = skill.strip()
                if skill:
                    skill_counts[skill] = skill_counts.get(skill, 0) + 1
        top_skills_sorted = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        top_skills = [{"skill": s, "count": c, "study_link": get_learning_link(s)} for s, c in top_skills_sorted]

    return {
        "total_jobs": total_jobs,
        "sources": sources,
        "top_locations": top_locations,
        "top_domains": top_domains,
        "salary_percentiles": salary_percentiles,
        "experience_distribution": experience_distribution,
        "top_skills": top_skills,
    }


def _compute_salary_percentiles(rows) -> dict:
    if not rows:
        return {"p25": None, "p50": None, "p75": None, "p90": None, "sample_size": 0}
    midpoints = sorted((r["salary_min"] + r["salary_max"]) / 2 for r in rows)
    n = len(midpoints)

    def percentile(p):
        idx = int(round((p / 100) * (n - 1)))
        return round(midpoints[idx], 2)

    return {
        "p25": percentile(25),
        "p50": percentile(50),
        "p75": percentile(75),
        "p90": percentile(90),
        "sample_size": n,
    }


@router.get("/evaluation")
def get_evaluation():
    return run_evaluation()
