from app import create_app
from core import groq_client


def test_index_renders():
    app = create_app()
    client = app.test_client()
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"ForgeCV" in resp.data


def _fake_forged():
    return {
        "name": "Aman Khan",
        "contact": "a@x.com | +91 9999999999",
        "sections": [
            {"heading": "SUMMARY", "body": "Engineer."},
            {"heading": "TECHNICAL SKILLS", "body": "Languages: Python, Flask"},
            {"heading": "EDUCATION", "entries": [
                {"header": "MAIT", "subheader": "B.Tech", "date": "2026", "bullets": []}]},
            {"heading": "WORK EXPERIENCE", "entries": [
                {"header": "Intern", "subheader": "Acme", "date": "2024",
                 "bullets": ["Built a Python Flask API"]}]},
        ],
    }


def test_generate_returns_scores(monkeypatch):
    monkeypatch.setattr(groq_client, "forge_resume", lambda src, jd="": _fake_forged())
    monkeypatch.setattr(groq_client, "write_cover_letter", lambda r, jd: "Dear team,")

    app = create_app()
    client = app.test_client()
    resp = client.post("/generate", data={
        "name": "Aman", "email": "a@x.com", "phone": "+91 9999999999",
        "skills": "Python, Flask", "experience": "Built an API",
        "job_description": "Python developer with Flask",
    })
    assert resp.status_code == 200
    assert b"100" in resp.data          # parse-ability gauge
    assert b"EDUCATION" in resp.data    # structured preview rendered


def test_download_after_generate(monkeypatch):
    monkeypatch.setattr(groq_client, "forge_resume", lambda src, jd="": _fake_forged())
    app = create_app()
    client = app.test_client()
    client.post("/generate", data={"name": "Aman", "job_description": ""})
    pdf = client.get("/download/pdf")
    docx = client.get("/download/docx")
    assert pdf.status_code == 200 and pdf.data[:4] == b"%PDF"
    assert docx.status_code == 200 and len(docx.data) > 0
