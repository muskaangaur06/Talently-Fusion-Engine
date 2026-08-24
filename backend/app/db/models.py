from dataclasses import dataclass
from typing import Optional


@dataclass
class Job:
    job_id: str
    company_name: str
    title: str
    description: str
    formatted_description: str
    location: str
    source: str
    posted_at: str
    salary_min: Optional[float]
    salary_max: Optional[float]
    experience_min: Optional[int]
    experience_max: Optional[int]
    skills: str
    apply_link: str
    domain: str
    employment_type: str
    fingerprint: str
    created_at: str

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "company_name": self.company_name,
            "title": self.title,
            "description": self.description,
            "formatted_description": self.formatted_description,
            "location": self.location,
            "source": self.source,
            "posted_at": self.posted_at,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "experience_min": self.experience_min,
            "experience_max": self.experience_max,
            "skills": [s.strip() for s in self.skills.split(",") if s.strip()] if self.skills else [],
            "apply_link": self.apply_link,
            "domain": self.domain,
            "employment_type": self.employment_type,
            "created_at": self.created_at,
        }


def row_to_job_dict(row) -> dict:
    skills_raw = row["skills"] or ""
    return {
        "job_id": row["job_id"],
        "company_name": row["company_name"],
        "title": row["title"],
        "description": row["description"],
        "formatted_description": row["formatted_description"],
        "location": row["location"],
        "source": row["source"],
        "posted_at": row["posted_at"],
        "salary_min": row["salary_min"],
        "salary_max": row["salary_max"],
        "experience_min": row["experience_min"],
        "experience_max": row["experience_max"],
        "skills": [s.strip() for s in skills_raw.split(",") if s.strip()],
        "apply_link": row["apply_link"],
        "domain": row["domain"],
        "employment_type": row["employment_type"],
        "created_at": row["created_at"],
    }
