from core.models import ResumeData, Experience, Education, JobSpec
from core import generator


def test_loop_stops_when_score_hits_target(monkeypatch):
    r = ResumeData(name="Aman", email="a@x.com", phone="+91 9999999999",
                   skills=["Python"], experiences=[Experience(bullets=["did x"])],
                   educations=[Education(degree="BTech")])
    job = JobSpec(target_keywords=[("python", 1), ("docker", 1)])

    calls = {"n": 0}

    def fake_rewrite(bullets, keywords):
        calls["n"] += 1
        return ["Built Python and Docker services"]

    monkeypatch.setattr(generator.groq_client, "rewrite_bullets", fake_rewrite)

    result, report = generator.generate(r, job)
    assert report.combined(0.5, 0.5) >= 99
    assert calls["n"] >= 1


def test_loop_respects_max_retries(monkeypatch):
    r = ResumeData(name="Aman", email="a@x.com", phone="+91 9999999999",
                   skills=["Python"],
                   experiences=[Experience(bullets=["did x"])],
                   educations=[Education(degree="BTech")])
    job = JobSpec(target_keywords=[("nonexistentskill", 5)])

    monkeypatch.setattr(generator.groq_client, "rewrite_bullets",
                        lambda bullets, keywords: ["did x"])  # never improves

    result, report = generator.generate(r, job, max_retries=3)
    assert report.match_score < 99
