import re
from core.models import ResumeData, JobSpec, ScoreReport

SYNONYMS = {
    "js": "javascript", "ts": "typescript", "py": "python",
    "postgres": "postgresql", "k8s": "kubernetes",
}


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
