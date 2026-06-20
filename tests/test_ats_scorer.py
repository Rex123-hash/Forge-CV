from core.models import ResumeData, Experience, Education, JobSpec
from core.ats_scorer import score_parse, score_match, score_resume


def _good_resume():
    return ResumeData(
        name="Aman K", email="a@x.com", phone="+91 9999999999",
        summary="Software engineer with Python and Flask.",
        skills=["Python", "Flask", "Docker", "SQL"],
        experiences=[Experience(title="Intern", company="Acme",
                                start="2024", end="2025",
                                bullets=["Built a Python REST API with Flask"])],
        educations=[Education(degree="BTech", institution="XYZ", year="2026")],
    )


def test_parse_score_perfect_for_clean_resume():
    assert score_parse(_good_resume()) >= 99


def test_parse_score_penalizes_missing_contact():
    r = _good_resume()
    r.email = ""
    r.phone = ""
    assert score_parse(r) < 99


def test_match_score_full_when_all_keywords_present():
    r = _good_resume()
    jd = JobSpec(target_keywords=[("python", 3), ("flask", 2), ("docker", 1)])
    score, missing = score_match(r, jd)
    assert score == 100
    assert missing == []


def test_match_score_reports_missing():
    r = _good_resume()
    jd = JobSpec(target_keywords=[("python", 3), ("kubernetes", 2)])
    score, missing = score_match(r, jd)
    assert "kubernetes" in missing
    assert score < 100


def test_score_resume_combines_both():
    r = _good_resume()
    jd = JobSpec(target_keywords=[("python", 1), ("flask", 1)])
    report = score_resume(r, jd)
    assert report.parse_score >= 99
    assert report.match_score == 100
