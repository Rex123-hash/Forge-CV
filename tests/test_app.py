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
    monkeypatch.setattr(groq_client, "extract_job_keywords", lambda jd: ["Python", "Flask"])

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


def test_score_is_honest_not_force_injected(monkeypatch):
    # resume genuinely lacks "Kubernetes"; we must NOT fake-inject it to hit 100.
    monkeypatch.setattr(groq_client, "forge_resume", lambda src, jd="": {
        "name": "Aman", "contact": "a@x.com",
        "sections": [{"heading": "TECHNICAL SKILLS", "body": "Languages: Python"}]})
    monkeypatch.setattr(groq_client, "extract_job_keywords", lambda jd: ["Python", "Kubernetes"])
    monkeypatch.setattr(groq_client, "write_cover_letter", lambda r, jd: "")

    client = create_app().test_client()
    resp = client.post("/generate", data={"name": "Aman", "job_description": "k8s role"})
    assert resp.status_code == 200
    assert b"Additional:" not in resp.data    # no artificial keyword stuffing
    assert b"Kubernetes" in resp.data         # shown as a missing keyword to add


def test_strip_keeps_dashes_removes_emoji():
    from core.groq_client import _strip
    # Per the resume spec, em/en dashes are kept; only emojis are removed.
    assert _strip("Top 106 — selected; Jun – Aug") == "Top 106 — selected; Jun – Aug"


def test_parse_autofill_returns_fields(monkeypatch):
    from core import parser
    monkeypatch.setattr(parser, "extract_text", lambda b, name: "resume text")
    monkeypatch.setattr(groq_client, "parse_resume", lambda text: {
        "name": "Amaan Khan", "email": "a@x.com", "phone": "+91",
        "skills": ["Python", "XGBoost"],
        "experiences": [{"title": "ML Intern", "company": "MAIT", "bullets": ["Built models"]}],
    })
    app = create_app()
    client = app.test_client()
    import io
    data = {"resume_file": (io.BytesIO(b"dummy"), "resume.pdf")}
    resp = client.post("/parse", data=data, content_type="multipart/form-data")
    j = resp.get_json()
    assert j["ok"] is True
    assert j["name"] == "Amaan Khan"
    assert "Python" in j["skills"]
    assert "Built models" in j["experience"]


def test_parse_no_file_returns_400():
    app = create_app()
    client = app.test_client()
    resp = client.post("/parse", data={}, content_type="multipart/form-data")
    assert resp.status_code == 400


def test_faq_renders():
    app = create_app()
    resp = app.test_client().get("/faq")
    assert resp.status_code == 200
    assert b"ATS" in resp.data


def test_stateless_resume_download():
    import json
    app = create_app()
    client = app.test_client()
    payload = json.dumps(_fake_forged())
    pdf = client.post("/download/resume/pdf", data={"resume": payload})
    docx = client.post("/download/resume/docx", data={"resume": payload})
    assert pdf.status_code == 200 and pdf.data[:4] == b"%PDF"
    assert docx.status_code == 200 and len(docx.data) > 100


def test_stateless_cover_download():
    app = create_app()
    client = app.test_client()
    pdf = client.post("/download/cover/pdf",
                      data={"cover": "Dear team,\n\nI am keen.", "name": "Aman"})
    docx = client.post("/download/cover/docx",
                       data={"cover": "Dear team,\n\nI am keen.", "name": "Aman"})
    assert pdf.status_code == 200 and pdf.data[:4] == b"%PDF"
    assert docx.status_code == 200 and len(docx.data) > 100


def test_download_missing_data_is_400():
    app = create_app()
    client = app.test_client()
    assert client.post("/download/resume/pdf", data={"resume": "{}"}).status_code == 400
    assert client.post("/download/cover/pdf", data={"cover": ""}).status_code == 400
