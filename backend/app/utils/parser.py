"""Multi-format resume text extraction: PDF, DOCX, and plain text."""
import io


def extract_text_from_pdf(file_bytes: bytes) -> str:
    import fitz  # PyMuPDF

    text_parts = []
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts)


def extract_text_from_docx(file_bytes: bytes) -> str:
    from docx import Document

    doc = Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs)


def extract_resume_text(filename: str, file_bytes: bytes) -> str:
    lower = filename.lower()
    try:
        if lower.endswith(".pdf"):
            return extract_text_from_pdf(file_bytes)
        if lower.endswith(".docx"):
            return extract_text_from_docx(file_bytes)
        if lower.endswith(".txt") or lower.endswith(".md"):
            return file_bytes.decode("utf-8", errors="replace")
    except ValueError:
        raise
    except Exception as exc:
        # A corrupted PDF (fitz) or a non-DOCX file wearing a .docx extension
        # (python-docx's PackageNotFoundError) would otherwise surface as an
        # unhandled 500 on the upload endpoint - the most user-input-heavy path
        # in the app. Normalize to the same ValueError the caller already
        # turns into a clean 400.
        raise ValueError(f"Could not read {filename}: the file may be corrupted or not a valid {lower.rsplit('.', 1)[-1].upper()} file.") from exc
    raise ValueError(f"Unsupported resume file type: {filename}")


COMMON_SKILLS = [
    "python", "java", "javascript", "typescript", "sql", "react", "node.js", "aws", "azure", "gcp",
    "docker", "kubernetes", "machine learning", "deep learning", "pytorch", "tensorflow", "pandas",
    "numpy", "scikit-learn", "nlp", "data analysis", "excel", "power bi", "tableau", "django",
    "fastapi", "flask", "spring", "c++", "c#", "go", "rust", "html", "css", "git", "linux",
    "rest api", "graphql", "mongodb", "postgresql", "mysql", "redis", "spark", "hadoop",
    "communication", "leadership", "project management", "agile", "scrum",
]


def extract_skills_from_text(text: str) -> list:
    text_lower = text.lower()
    found = []
    for skill in COMMON_SKILLS:
        if skill in text_lower:
            found.append(skill)
    return found


def extract_experience_years(text: str) -> int:
    import re

    matches = re.findall(r"(\d+)\+?\s*(?:years|yrs)\s*(?:of)?\s*experience", text.lower())
    if matches:
        return max(int(m) for m in matches)
    return 0
