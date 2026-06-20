from core.models import ResumeData, Experience, Education, JobSpec, ScoreReport


def test_resume_data_defaults():
    r = ResumeData(name="Aman", email="a@x.com", phone="+91 99999 99999")
    assert r.name == "Aman"
    assert r.experiences == []
    assert r.skills == []


def test_experience_fields():
    e = Experience(title="Intern", company="Acme", start="2024", end="2025",
                   bullets=["Built X"])
    assert e.bullets == ["Built X"]


def test_score_report_combined():
    s = ScoreReport(parse_score=100, match_score=98,
                    missing_keywords=["docker"], issues=[])
    assert s.combined(0.5, 0.5) == 99


def test_jobspec_holds_keywords():
    j = JobSpec(raw="...", target_keywords=[("python", 3), ("flask", 1)])
    assert j.target_keywords[0][0] == "python"
