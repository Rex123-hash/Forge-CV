import config
from core import groq_client
from core.ats_scorer import score_resume
from core.models import ResumeData, JobSpec, ScoreReport


def generate(resume: ResumeData, job: JobSpec,
             max_retries: int = config.MAX_RETRIES) -> tuple[ResumeData, ScoreReport]:
    """Rewrite bullets, score, and retry up to max_retries to reach TARGET_SCORE."""
    keywords = [t for t, _ in job.target_keywords]

    for attempt in range(max_retries + 1):
        for exp in resume.experiences:
            if exp.bullets:
                exp.bullets = groq_client.rewrite_bullets(exp.bullets, keywords)

        report = score_resume(resume, job)
        if report.combined(config.PARSE_WEIGHT, config.MATCH_WEIGHT) >= config.TARGET_SCORE:
            return resume, report

        keywords = report.missing_keywords or keywords
        if not report.missing_keywords:
            break

    return resume, score_resume(resume, job)
