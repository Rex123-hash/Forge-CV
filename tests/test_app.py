import io
from app import create_app


def test_index_renders():
    app = create_app()
    client = app.test_client()
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"ForgeCV" in resp.data


def test_generate_returns_scores(monkeypatch):
    import core.generator as gen
    from core.models import ResumeData, ScoreReport, Experience

    def fake_generate(resume, job, **kw):
        return (ResumeData(name="Aman", experiences=[Experience(bullets=["x"])]),
                ScoreReport(parse_score=100, match_score=99, missing_keywords=[]))
    monkeypatch.setattr(gen, "generate", fake_generate)

    app = create_app()
    client = app.test_client()
    resp = client.post("/generate", data={
        "name": "Aman", "email": "a@x.com", "phone": "+91 9999999999",
        "skills": "Python, Flask", "experience": "Built an API",
        "job_description": "Python developer with Flask",
    })
    assert resp.status_code == 200
    assert b"99" in resp.data
