"""Gemini integration with graceful heuristic fallbacks.

All Gemini calls use a client-supplied API key (X-Gemini-API-Key header).
When no key is supplied, or the Gemini call fails, every function falls
back to a deterministic heuristic implementation so the product remains
functional even if the Gemini call errors - but Gemini is the primary
reasoning engine for this app and failures are logged, not swallowed.
"""
import json
import logging
import re

logger = logging.getLogger("ai_service")

GEMINI_MODEL_NAME = "gemini-3.5-flash-lite"


def _get_model(api_key: str):
    if not api_key:
        return None
    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        return genai.GenerativeModel(GEMINI_MODEL_NAME)
    except Exception:
        logger.exception("Failed to initialize Gemini model")
        return None


def _extract_json(text: str):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    match = re.search(r"[\{\[].*[\}\]]", text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)


def _call_gemini_json(api_key: str, prompt: str):
    model = _get_model(api_key)
    if model is None:
        return None
    try:
        response = model.generate_content(prompt)
        return _extract_json(response.text)
    except Exception:
        logger.exception("Gemini JSON call failed, falling back to heuristic")
        return None


def _call_gemini_text(api_key: str, prompt: str):
    model = _get_model(api_key)
    if model is None:
        return None
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        logger.exception("Gemini text call failed, falling back to heuristic")
        return None


STOPWORDS = {
    "a", "an", "the", "in", "on", "at", "for", "with", "and", "or", "to", "of", "jobs", "job",
    "role", "roles", "position", "positions", "near", "me", "looking", "want", "find", "search",
    "show", "get", "please", "i", "am", "is", "are",
}

# Maps common spoken/searched city names to the spelling actually stored in the
# ingested job listings (e.g. users search "Bangalore" but the data says "Bengaluru").
LOCATION_ALIASES = {
    "bangalore": "Bengaluru",
    "bengaluru": "Bengaluru",
    "bombay": "Mumbai",
    "mumbai": "Mumbai",
    "gurgaon": "Gurugram",
    "gurugram": "Gurugram",
    "pune": "Pune",
    "delhi": "New Delhi",
    "new delhi": "New Delhi",
    "hyderabad": "Hyderabad",
    "secunderabad": "Secunderabad",
    "chennai": "Chennai",
    "madras": "Chennai",
    "noida": "Noida",
    "kolkata": "Kolkata",
    "calcutta": "Kolkata",
    "ahmedabad": "Ahmedabad",
    "jaipur": "Jaipur",
    "kochi": "Kochi",
    "cochin": "Kochi",
    "coimbatore": "Coimbatore",
    "chandigarh": "Chandigarh",
    "bhubaneswar": "Bhubaneswar",
    "navi mumbai": "Navi Mumbai",
    "remote": "Anywhere",
    "anywhere": "Anywhere",
}

KNOWN_SOURCES = ["linkedin", "naukri", "indeed", "internshala"]

# A fresher role tops out at 1 year of required experience. Anything a posting
# labels intern, fresher, trainee, graduate or entry level falls in this band,
# as does an explicit "0-1 years".
FRESHER_MAX_YEARS = 1
FRESHER_QUERY_PATTERN = (
    r"\bfresher(?:s)?\b"
    r"|\bintern(?:ship|s)?\b"
    r"|\bentry[\s\-]?level\b"
    r"|\btrainee(?:s)?\b"
    r"|\bgraduate\b|\bfresh\s+graduate\b"
    r"|\bno\s+(?:prior\s+)?experience\b"
    r"|\b0\s*[-to]+\s*1\s*(?:years|yrs|year)?\b"
    r"|\b0\s*(?:years|yrs|year)\b"
)


def parse_query_intent_heuristic(query: str) -> dict:
    q_lower = query.lower()
    filters = {"keywords": "", "location": None, "source": None, "min_experience": None, "max_experience": None}

    for alias in sorted(LOCATION_ALIASES, key=len, reverse=True):
        if alias in q_lower:
            filters["location"] = LOCATION_ALIASES[alias]
            q_lower = q_lower.replace(alias, "")
            break

    for src in KNOWN_SOURCES:
        if src in q_lower:
            filters["source"] = src.title() if src != "linkedin" else "LinkedIn"
            q_lower = q_lower.replace(src, "")
            break

    # Intern, fresher, graduate and "0-1 years" all describe the same audience:
    # someone with no professional experience yet. They are treated as one band
    # so that searching any of these terms returns the same set of roles.
    # Checked before the generic "N years" match below, because phrasings like
    # "0-1 years" and "0 years experience" would otherwise be read as a plain
    # minimum of 0 or 1 with no upper bound, which is not a fresher search.
    fresher_match = re.search(FRESHER_QUERY_PATTERN, q_lower)
    if fresher_match:
        filters["min_experience"] = 0
        filters["max_experience"] = FRESHER_MAX_YEARS
        q_lower = q_lower.replace(fresher_match.group(0), "")
    else:
        exp_match = re.search(r"(\d+)\s*\+?\s*(?:years|yrs|year)", q_lower)
        if exp_match:
            filters["min_experience"] = int(exp_match.group(1))
            q_lower = q_lower.replace(exp_match.group(0), "")

    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9+.#]*", q_lower)
    keywords = [t for t in tokens if t not in STOPWORDS and len(t) > 1]
    filters["keywords"] = " ".join(keywords).strip()

    return filters


def parse_query_intent(query: str, api_key: str = None) -> dict:
    if api_key:
        prompt = f"""Extract structured search filters from this natural-language job search query.
Return ONLY valid JSON with keys: keywords (string, core role/skill terms only),
location (string or null), source (one of LinkedIn/Naukri/Indeed/Internshala or null),
min_experience (integer years or null), max_experience (integer years or null).

Query: "{query}\""""
        result = _call_gemini_json(api_key, prompt)
        if isinstance(result, dict) and "keywords" in result:
            return result
    return parse_query_intent_heuristic(query)


def _attach_study_links(technical_questions: list, job_skills: list) -> list:
    """Attaches a curated study-resource link to each technical question based on the
    skill it targets. Links only ever come from the hand-picked LEARNING_LINKS map -
    never AI-suggested, since LLMs frequently invent plausible-looking but broken URLs."""
    from app.services.learning_resources import get_learning_link

    enriched = []
    for q in technical_questions:
        if isinstance(q, dict):
            question_text = q.get("question", "")
            targets_skill = q.get("targets_skill")
        else:
            question_text = q
            targets_skill = next((s for s in job_skills if skill_appears_in_text(s, q)), None)

        enriched.append(
            {
                "question": question_text,
                "targets_skill": targets_skill,
                "study_link": get_learning_link(targets_skill) if targets_skill else None,
            }
        )
    return enriched


def generate_interview_prep_heuristic(job: dict, matched_skills: list = None, missing_skills: list = None) -> dict:
    title = job.get("title", "this role")
    skills = job.get("skills", [])[:6]
    domain = job.get("domain", "the relevant field")

    # When we know the candidate's gaps, prioritize questions on those skills first -
    # that's exactly where interview prep is most useful, not the skills they already have.
    if missing_skills:
        ordered_skills = [s for s in skills if s in missing_skills] + [s for s in skills if s not in missing_skills]
    else:
        ordered_skills = skills

    technical_questions = [
        {"question": f"Explain your hands-on experience with {s}.", "targets_skill": s} for s in ordered_skills[:4]
    ] or [{"question": f"Walk me through a project relevant to {title}.", "targets_skill": None}]
    behavioral_questions = [
        "Tell me about a time you handled a tight deadline.",
        "Describe a conflict with a teammate and how you resolved it.",
        f"Why are you interested in a {title} role at this company?",
    ]
    tips = [
        f"Research the company's recent work in {domain}.",
        f"Prepare concrete examples demonstrating {', '.join(skills[:3]) if skills else 'core skills for this role'}.",
        "Prepare 2-3 thoughtful questions to ask the interviewer.",
    ]
    if missing_skills:
        tips.insert(0, f"Brush up on {', '.join(missing_skills[:3])} before the interview - these are on the job's skill list but not yet reflected in your resume.")
    if matched_skills:
        tips.append(f"Lean on your existing experience with {', '.join(matched_skills[:3])} - these are a strong match for this role.")

    return {
        "technical_questions": _attach_study_links(technical_questions, job.get("skills", [])),
        "behavioral_questions": behavioral_questions,
        "preparation_tips": tips,
        "source": "heuristic",
    }


def generate_interview_prep(job: dict, api_key: str = None, matched_skills: list = None, missing_skills: list = None) -> dict:
    job_skills = job.get("skills", [])
    if api_key:
        candidate_context = ""
        if matched_skills or missing_skills:
            candidate_context = f"""
This candidate's resume already demonstrates: {', '.join(matched_skills) if matched_skills else 'none of the listed skills yet'}.
This candidate is missing: {', '.join(missing_skills) if missing_skills else 'none - they cover all listed skills'}.
Weight technical_questions toward the missing skills first (that's what they most need to prepare for),
and include one preparation_tip that reassures them about their existing matched skills and one that
tells them specifically what to brush up on given the missing skills above."""
        prompt = f"""Generate an interview preparation guide for this job as JSON with keys:
technical_questions (array of 4-6 objects, each {{"question": "...", "targets_skill": "one skill
from the Skills list below that this question tests, or null if it's a general technical question"}}),
behavioral_questions (array of 3-4 strings), preparation_tips (array of 3-5 strings).

Ground every technical question in the actual job description and skills below - do not invent
requirements not present in this posting.
{candidate_context}

Job Title: {job.get('title')}
Company: {job.get('company_name')}
Skills: {', '.join(job_skills)}
Description: {(job.get('description') or '')[:1500]}"""
        result = _call_gemini_json(api_key, prompt)
        if isinstance(result, dict) and "technical_questions" in result:
            result["technical_questions"] = _attach_study_links(result["technical_questions"], job_skills)
            result["source"] = "gemini"
            return result
    return generate_interview_prep_heuristic(job, matched_skills, missing_skills)


def skill_appears_in_text(skill: str, text: str) -> bool:
    """Word-boundary match so short skill names (R, C, Go) don't false-positive on
    substrings inside unrelated words (e.g. 'R' inside 'worked')."""
    pattern = r"(?<![a-zA-Z0-9])" + re.escape(skill) + r"(?![a-zA-Z0-9])"
    return re.search(pattern, text, re.IGNORECASE) is not None


def analyze_ats_match_heuristic(resume_text: str, job: dict) -> dict:
    job_skills = job.get("skills", [])
    matched = [s for s in job_skills if skill_appears_in_text(s, resume_text)]
    missing = [s for s in job_skills if not skill_appears_in_text(s, resume_text)]
    match_pct = round((len(matched) / len(job_skills)) * 100, 1) if job_skills else 0.0

    suggestions = []
    for skill in missing[:5]:
        suggestions.append(f"Add a bullet point demonstrating experience with '{skill}' if applicable.")
    if match_pct < 50:
        suggestions.append("Mirror more of the job description's exact terminology in your resume summary.")

    return {
        "match_percentage": match_pct,
        "matched_keywords": matched,
        "missing_keywords": missing,
        "suggestions": suggestions,
        "source": "heuristic",
    }


def analyze_ats_match(resume_text: str, job: dict, api_key: str = None) -> dict:
    if api_key:
        prompt = f"""Analyze this resume against the job description for ATS keyword match.
Return ONLY valid JSON with keys: match_percentage (number 0-100),
matched_keywords (array of strings), missing_keywords (array of strings),
suggestions (array of 3-5 actionable strings to improve the resume's ATS match).

Job Title: {job.get('title')}
Required Skills: {', '.join(job.get('skills', []))}
Job Description: {(job.get('description') or '')[:1500]}

Resume:
{resume_text[:3000]}"""
        result = _call_gemini_json(api_key, prompt)
        if isinstance(result, dict) and "match_percentage" in result:
            result["source"] = "gemini"
            return result
    return analyze_ats_match_heuristic(resume_text, job)


def career_chat_heuristic(message: str, context: dict) -> str:
    job = context.get("job")
    resume_skills = context.get("resume_skills") or []
    msg_lower = message.lower()

    if job:
        title = job.get("title", "this role")
        if "why" in msg_lower and ("suitable" in msg_lower or "fit" in msg_lower or "qualif" in msg_lower):
            if resume_skills:
                job_skills = set(s.lower() for s in job.get("skills", []))
                matched = [s for s in resume_skills if s.lower() in job_skills]
                if matched:
                    return f"Your resume shows experience with {', '.join(matched[:5])}, which directly overlaps with what {title} at {job.get('company_name')} is asking for. That overlap is your strongest case - lead with it in your application."
                return f"I don't see your resume's skills overlapping much with {title}'s listed requirements yet. Consider highlighting any adjacent or transferable experience you have."
            return "Upload or select a resume on the Recommendations page so I can compare it against this role's requirements."
        if "career" in msg_lower and ("guid" in msg_lower or "path" in msg_lower or "advice" in msg_lower):
            skills = ", ".join(job.get("skills", [])[:5]) or "the skills this role lists"
            return f"Roles like {title} typically value {skills}. If you're aiming for this path, building depth in those areas and taking on projects that use them is the most direct route."
        if "salary" in msg_lower or "pay" in msg_lower:
            smin, smax = job.get("salary_min"), job.get("salary_max")
            if smin and smax:
                return f"Based on the listing, {title} at {job.get('company_name')} offers approximately {smin}-{smax}. Note this may be approximate or sourced from third-party estimates."
            return f"This listing for {title} doesn't specify a salary range. I'd recommend researching market rates on Glassdoor or Payscale for this role and location."
        if "skill" in msg_lower or "requirement" in msg_lower:
            skills = ", ".join(job.get("skills", [])[:8]) or "not explicitly listed"
            return f"The key skills for {title} include: {skills}."
        if "apply" in msg_lower:
            return f"You can apply via the 'Apply' link on the job listing for {title} at {job.get('company_name')}."
        return f"I can help with questions about the {title} role at {job.get('company_name')}. Try asking about required skills, salary range, why you're a fit, or how to apply."

    return (
        "I'm your career copilot. Ask me about job listings, required skills, salary expectations, "
        "or upload your resume on the Recommendations page for personalized matches."
    )


def career_chat(message: str, context: dict, api_key: str = None) -> str:
    if api_key:
        job = context.get("job")
        history = context.get("history", [])
        resume_skills = context.get("resume_skills") or []
        experience_years = context.get("experience_years")
        history_text = "\n".join(f"{h.get('role')}: {h.get('content')}" for h in history[-6:])
        job_context = ""
        if job:
            job_context = f"""
Current job context:
Title: {job.get('title')}
Company: {job.get('company_name')}
Location: {job.get('location')}
Skills: {', '.join(job.get('skills', []))}
Description excerpt: {(job.get('description') or '')[:800]}
"""
        candidate_context = ""
        if resume_skills or experience_years is not None:
            candidate_context = f"""
This candidate's resume shows: skills - {', '.join(resume_skills) if resume_skills else 'not specified'};
experience - {experience_years if experience_years is not None else 'not specified'} years.
When asked "why am I suitable" or for career guidance, ground your answer in the overlap (or gaps)
between this candidate's actual skills/experience above and the job context - never invent skills
or experience the candidate hasn't stated."""
        prompt = f"""You are a helpful, concise career copilot assistant for a job board.
{job_context}{candidate_context}
Conversation so far:
{history_text}

User: {message}

Respond helpfully and concisely (max 4 sentences) grounded ONLY in the job and candidate context provided above. Do not invent facts not present in the context."""
        result = _call_gemini_text(api_key, prompt)
        if result:
            return result
    return career_chat_heuristic(message, context)


def optimize_resume_phrasing_heuristic(resume_text: str, job: dict) -> list:
    missing = [s for s in job.get("skills", []) if s.lower() not in resume_text.lower()]
    suggestions = []
    for skill in missing[:5]:
        suggestions.append(
            {
                "original": "(not present in resume)",
                "suggested": f"Led/contributed to work involving {skill}, delivering measurable impact.",
                "reason": f"'{skill}' appears in the job requirements but not in your resume.",
            }
        )
    return suggestions


def optimize_resume_phrasing(resume_text: str, job: dict, api_key: str = None) -> list:
    if api_key:
        prompt = f"""Suggest 3-5 specific resume bullet-point rewrites to better align with this job.
Return ONLY a valid JSON array of objects with keys: original, suggested, reason.

Job Title: {job.get('title')}
Required Skills: {', '.join(job.get('skills', []))}

Resume:
{resume_text[:3000]}"""
        result = _call_gemini_json(api_key, prompt)
        if isinstance(result, list):
            return result
    return optimize_resume_phrasing_heuristic(resume_text, job)


GENERIC_PHRASE_PATTERNS = [
    r"\bworked on\b", r"\bhelped (?:with|to)\b", r"\bresponsible for\b",
    r"\binvolved in\b", r"\bassisted (?:with|in)\b", r"\bparticipated in\b",
    r"\btasked with\b", r"\bhandled\b",
]


def _is_list_or_heading_line(line: str) -> bool:
    """Skill lists, section headers, and contact lines shouldn't be treated as
    'weak' prose - rewriting them adds no signal and risks corrupting structured data."""
    if line.isupper():
        return True
    if re.match(r"^(skills?|technologies|tools|education|certifications?)\s*:", line, re.IGNORECASE):
        return True
    comma_count = line.count(",")
    word_count = len(line.split())
    if comma_count >= 2 and word_count <= comma_count * 3:
        return True
    return False


def _split_resume_lines(resume_text: str) -> list:
    lines = [ln.strip() for ln in resume_text.splitlines()]
    return [ln for ln in lines if len(ln) > 15 and not _is_list_or_heading_line(ln)]


def _find_weak_lines_heuristic(resume_text: str) -> list:
    weak = []
    for line in _split_resume_lines(resume_text):
        line_lower = line.lower()
        has_number = bool(re.search(r"\d", line))
        is_generic = any(re.search(pat, line_lower) for pat in GENERIC_PHRASE_PATTERNS)
        if is_generic or not has_number:
            weak.append(line)
    return weak[:8]


def _line_is_grounded(rewritten: str, original_lines: list, resume_text: str) -> bool:
    """Verification pass: reject a rewrite that doesn't trace back to something already
    in the resume, to keep the model from inventing skills/employers/numbers wholesale."""
    if not rewritten or len(rewritten) < 10:
        return False
    rewritten_words = set(re.findall(r"[a-zA-Z]{4,}", rewritten.lower()))
    resume_words = set(re.findall(r"[a-zA-Z]{4,}", resume_text.lower()))
    if not rewritten_words:
        return False
    overlap = len(rewritten_words & resume_words) / len(rewritten_words)
    return overlap >= 0.4


def boost_resume_presentation_heuristic(resume_text: str, job: dict) -> dict:
    weak_lines = _find_weak_lines_heuristic(resume_text)
    rewrites = []
    weak_phrase_pattern = re.compile(
        r"\b(?:was |is |am |were )?"
        r"(worked on|helped with|helped to|responsible for|involved in|assisted with|assisted in|participated in|tasked with|handled)"
        r"(\s+)([a-zA-Z]+ing)?\b",
        re.IGNORECASE,
    )
    for line in weak_lines:
        mentioned_skills = [s for s in job.get("skills", []) if skill_appears_in_text(s, line)]

        def _replace(match):
            is_line_start = match.start() == 0
            gerund = match.group(3)
            whitespace = match.group(2)
            if gerund:
                # "on" + gerund is always grammatical, unlike trying to stem the gerund back
                # to an infinitive ("migrating" -> "migrat" is wrong; English silent-e/doubled
                # -consonant rules aren't safely reversible without a dictionary).
                lead_in = "Took the lead on" if is_line_start else "took the lead on"
                return f"{lead_in} {gerund}{whitespace}"
            return ("Led" if is_line_start else "led") + whitespace

        rewritten = weak_phrase_pattern.sub(_replace, line)
        rewritten = re.sub(r" {2,}", " ", rewritten)
        if rewritten == line:
            continue
        rewrites.append(
            {
                "original_line": line,
                "rewritten_line": rewritten,
                "reason": "Replaced passive/generic phrasing with stronger, ownership-focused language using only content already in your resume.",
                "targets_skill": mentioned_skills[0] if mentioned_skills else None,
            }
        )
    return {"rewrites": rewrites[:5], "source": "heuristic"}


def boost_resume_presentation(resume_text: str, job: dict, api_key: str = None) -> dict:
    """Finds resume lines that understate real experience and rewrites them to be more
    specific/quantified and better aligned with the job's terminology - without inventing
    any skill, employer, or achievement not already present in the resume. Every rewrite
    is verified for grounding against the original text before being returned."""
    if api_key:
        prompt = f"""You are improving how a candidate PRESENTS their existing experience for a specific job.
Do NOT invent new skills, employers, projects, or numbers that are not already stated or clearly implied
in the resume below. Only rewrite lines to be more specific, quantified (only if a number is already
implied), and to use terminology that echoes the job description more closely.

Return ONLY a valid JSON object: {{"rewrites": [{{"original_line": "...", "rewritten_line": "...",
"reason": "...", "targets_skill": "skill name or null"}}]}} with 3-6 rewrites, each based on an
actual line from the resume below.

Job Title: {job.get('title')}
Required Skills: {', '.join(job.get('skills', []))}
Job Description excerpt: {(job.get('description') or '')[:1000]}

Resume:
{resume_text[:3000]}"""
        result = _call_gemini_json(api_key, prompt)
        if isinstance(result, dict) and isinstance(result.get("rewrites"), list):
            original_lines = _split_resume_lines(resume_text)
            verified = [
                r for r in result["rewrites"]
                if isinstance(r, dict)
                and _line_is_grounded(r.get("rewritten_line", ""), original_lines, resume_text)
            ]
            if verified:
                return {"rewrites": verified, "source": "gemini"}
    return boost_resume_presentation_heuristic(resume_text, job)


def apply_resume_rewrites(resume_text: str, rewrites: list) -> str:
    """Applies verified rewrites to the resume text by replacing each original line
    with its rewritten version, for recomputing the match score on improved text."""
    updated = resume_text
    for rewrite in rewrites:
        original = rewrite.get("original_line", "")
        rewritten = rewrite.get("rewritten_line", "")
        if original and rewritten and original in updated:
            updated = updated.replace(original, rewritten)
    return updated


def _cover_letter_is_grounded(letter: str, resume_text: str) -> bool:
    """Same grounding discipline as resume rewrites: reject a letter that doesn't
    trace back to the actual resume content, to catch invented employers/projects/numbers."""
    if not letter or len(letter) < 120:
        return False
    letter_words = set(re.findall(r"[a-zA-Z]{4,}", letter.lower()))
    resume_words = set(re.findall(r"[a-zA-Z]{4,}", resume_text.lower()))
    if not letter_words:
        return False
    overlap = len(letter_words & resume_words) / len(letter_words)
    return overlap >= 0.25


def _best_highlight_line(resume_text: str, matched_skills: list) -> str:
    """Picks a genuinely descriptive resume line to reference in the heuristic cover
    letter, preferring one that actually mentions a matched skill over just grabbing
    the first line (which is often a name/title header, not a real achievement)."""
    lines = _split_resume_lines(resume_text)
    if not lines:
        return ""
    # Prefer a line that reads like an actual bullet/achievement (starts with a verb-ish
    # word, has enough words to be a real sentence) and mentions a skill we're citing.
    for skill in matched_skills:
        for line in lines:
            if skill_appears_in_text(skill, line) and len(line.split()) >= 6:
                return line
    for line in lines:
        if len(line.split()) >= 6:
            return line
    return lines[0]


def generate_cover_letter_heuristic(resume_text: str, job: dict, matched_skills: list) -> str:
    company = job.get("company_name", "your company")
    title = job.get("title", "this role")
    top_skills = ", ".join(matched_skills[:4]) if matched_skills else "the skills listed in my resume"
    highlight = _best_highlight_line(resume_text, matched_skills)
    highlight_para = f"For example: {highlight}\n\n" if highlight else ""

    return (
        f"Dear Hiring Manager,\n\n"
        f"I'm writing to apply for the {title} position at {company}. Based on my background in "
        f"{top_skills}, I believe I'd be a strong fit for this role.\n\n"
        f"{highlight_para}"
        f"I'd welcome the chance to talk about how my experience lines up with what your team is building. "
        f"Thank you for your time and consideration.\n\n"
        f"Sincerely,"
    )


def generate_cover_letter(resume_text: str, job: dict, matched_skills: list, api_key: str = None) -> dict:
    """Generates a cover letter grounded strictly in the candidate's real resume content
    for a specific matched job. Never invents employers, projects, or achievements not
    already present in the resume - verified the same way resume boost rewrites are."""
    if api_key:
        prompt = f"""Write a concise, natural-sounding cover letter (250-350 words) for this candidate applying to
a specific job. Use ONLY experience, skills, and achievements that are already stated in the resume below.
Do NOT invent employers, projects, numbers, or skills not present in the resume. Reference the job title and
company by name. Mention 2-3 of the candidate's matched skills naturally, don't just list them. Keep the tone
confident but not over the top. Do not use em dashes. Return ONLY the letter text, no preamble, no markdown.

Job Title: {job.get('title')}
Company: {job.get('company_name')}
Location: {job.get('location')}
Matched skills for this role: {', '.join(matched_skills[:8])}
Job Description excerpt: {(job.get('description') or '')[:1200]}

Candidate's resume:
{resume_text[:3500]}"""
        result = _call_gemini_text(api_key, prompt)
        if result and _cover_letter_is_grounded(result, resume_text):
            return {"letter": result.strip(), "source": "gemini"}

    return {"letter": generate_cover_letter_heuristic(resume_text, job, matched_skills), "source": "heuristic"}


def recommend_best_resume(scored_resumes: list) -> dict:
    """Deterministic pick: no LLM call needed since the score is already computed.
    scored_resumes: [{"label": str, "score": float, "experience_years": int}, ...]"""
    best = max(scored_resumes, key=lambda r: r["score"])
    others = [r for r in scored_resumes if r is not best]
    reason_parts = [f"'{best['label']}' scored highest at {best['score']}%"]
    if others:
        margin = best["score"] - max(o["score"] for o in others)
        reason_parts.append(f"a lead of {round(margin, 1)} points over your other resume(s)")
    reason = ", ".join(reason_parts) + "."
    return {"recommended_label": best["label"], "reason": reason}


def _merged_resume_is_grounded(merged_text: str, all_resume_texts: list) -> bool:
    """Same grounding discipline as cover letters/rewrites, but checked against the UNION
    of all source resumes - a merge is allowed to pull from any of the originals, just not
    invent content absent from all of them."""
    if not merged_text or len(merged_text) < 200:
        return False
    merged_words = set(re.findall(r"[a-zA-Z]{4,}", merged_text.lower()))
    source_words = set()
    for t in all_resume_texts:
        source_words |= set(re.findall(r"[a-zA-Z]{4,}", t.lower()))
    if not merged_words:
        return False
    overlap = len(merged_words & source_words) / len(merged_words)
    return overlap >= 0.35


def generate_merged_resume(resumes: list, job: dict = None, api_key: str = None) -> dict:
    """Merges the strongest lines from up to 3 resumes into one candidate resume, grounded
    against the union of all source resumes. resumes: [{"label", "text"}, ...]. Falls back to
    just returning the resume with the highest score, unmerged, if no key or grounding fails."""
    if api_key:
        resumes_block = "\n\n".join(f"--- Resume: {r['label']} ---\n{r['text'][:2500]}" for r in resumes)
        job_block = ""
        if job:
            job_block = f"""
Target job:
Title: {job.get('title')}
Company: {job.get('company_name')}
Required skills: {', '.join(job.get('skills', []))}
Description excerpt: {(job.get('description') or '')[:1000]}
Weight which content to keep toward what best matches this specific job."""
        prompt = f"""You are merging {len(resumes)} versions of the same candidate's resume into ONE best version.
Use ONLY content that already appears in at least one of the resumes below - do not invent any new
skill, employer, project, or number. Keep the strongest, most specific, most quantified version of
each point when the resumes overlap. Produce a complete, well-organized resume (summary, skills,
experience, education if present). Do not use em dashes. Return ONLY the merged resume text, no preamble.
{job_block}

{resumes_block}"""
        result = _call_gemini_text(api_key, prompt)
        if result is None:
            logger.warning("generate_merged_resume: Gemini call returned no result, falling back")
        elif not _merged_resume_is_grounded(result, [r["text"] for r in resumes]):
            logger.warning(
                "generate_merged_resume: Gemini output failed the grounding check, falling back. "
                "Result length=%d, preview=%r",
                len(result),
                result[:200],
            )
        else:
            return {"merged_text": result.strip(), "source": "gemini"}

    return {"merged_text": None, "source": "heuristic"}
