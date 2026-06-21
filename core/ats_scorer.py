import re
from core.models import ResumeData, JobSpec, ScoreReport

SYNONYMS = {
    "js": "javascript", "ts": "typescript", "py": "python",
    "postgres": "postgresql", "k8s": "kubernetes",
    "ml": "machine learning", "ai": "artificial intelligence",
    "nlp": "natural language processing", "dl": "deep learning",
    "cv": "computer vision", "ci/cd": "continuous integration",
    "gcp": "google cloud", "oop": "object oriented",
}


def struct_text(d: dict) -> str:
    """Flatten a structured (section-based) resume dict to plain text."""
    parts = [d.get("name", ""), d.get("contact", "")]
    for s in d.get("sections", []) or []:
        parts.append(s.get("heading", ""))
        if s.get("body"):
            parts.append(s["body"])
        for e in s.get("entries", []) or []:
            parts += [e.get("header", ""), e.get("subheader", ""), e.get("date", "")]
            parts += e.get("bullets", []) or []
    return "\n".join(p for p in parts if p)


def score_struct(d: dict, job: JobSpec) -> ScoreReport:
    """Score a structured resume dict: parse-ability + job-match."""
    text = struct_text(d).lower()
    headings = " ".join((s.get("heading", "") for s in d.get("sections", []) or [])).upper()

    parse = 100
    if "@" not in d.get("contact", ""):
        parse -= 15
    if not d.get("name"):
        parse -= 15
    if "EDUCATION" not in headings:
        parse -= 15
    if "SKILL" not in headings:
        parse -= 15
    if not any(k in headings for k in ("EXPERIENCE", "PROJECT", "RESEARCH", "WORK")):
        parse -= 15
    parse = max(0, parse)

    if job.target_keywords:
        total = sum(w for _, w in job.target_keywords)
        covered, missing = 0, []
        for term, weight in job.target_keywords:
            canonical = SYNONYMS.get(term, term)
            if canonical in text or term in text:
                covered += weight
            else:
                missing.append(term)
        match = round(100 * covered / total) if total else 100
    else:
        match, missing = 100, []

    issues = [] if parse == 100 else ["Resume missing a standard section or contact info."]
    return ScoreReport(parse_score=parse, match_score=match,
                       missing_keywords=missing, issues=issues)


def _resume_text(r: ResumeData) -> str:
    parts = [r.name, r.summary, " ".join(r.skills), " ".join(r.projects)]
    for e in r.experiences:
        parts += [e.title, e.company, " ".join(e.bullets)]
    for ed in r.educations:
        parts += [ed.degree, ed.institution]
    return " ".join(parts).lower()


def score_parse(r: ResumeData) -> int:
    """Job-independent: can an ATS cleanly read this resume?"""
    score = 100
    if not (r.email and re.match(r"[^@]+@[^@]+\.[^@]+", r.email)):
        score -= 20
    if not r.phone:
        score -= 10
    if not r.experiences:
        score -= 25
    if not r.educations:
        score -= 15
    if not r.skills:
        score -= 15
    if not r.name:
        score -= 15
    return max(0, score)


def score_match(r: ResumeData, job: JobSpec) -> tuple[int, list[str]]:
    """Job-dependent: weighted coverage of target keywords."""
    if not job.target_keywords:
        return 100, []
    text = _resume_text(r)
    total = sum(w for _, w in job.target_keywords)
    covered = 0
    missing = []
    for term, weight in job.target_keywords:
        canonical = SYNONYMS.get(term, term)
        if canonical in text or term in text:
            covered += weight
        else:
            missing.append(term)
    score = round(100 * covered / total) if total else 100
    return score, missing


def score_resume(r: ResumeData, job: JobSpec) -> ScoreReport:
    parse = score_parse(r)
    match, missing = score_match(r, job)
    issues = []
    if parse < 100:
        issues.append("Resume missing standard sections or contact info.")
    return ScoreReport(parse_score=parse, match_score=match,
                       missing_keywords=missing, issues=issues)
