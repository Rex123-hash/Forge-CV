from flask import Flask, render_template, request, send_file
from io import BytesIO
from types import SimpleNamespace
import config
from core.models import JobSpec
from core.keyword_extractor import extract_keywords
from core import parser, groq_client
from core.ats_scorer import score_struct
from core.resume_builder import build_docx_from_dict
from core.pdf_export import build_pdf_from_dict

_last = {}  # in-memory last result for downloads (stateless per process)


def _assemble_source(form) -> str:
    """Build a plain-text source from the manual form fields."""
    parts = []
    if form.get("name"):
        parts.append(form["name"])
    contact = " | ".join(x for x in [form.get("email", ""), form.get("phone", "")] if x)
    if contact:
        parts.append(contact)
    if form.get("skills"):
        parts.append("SKILLS\n" + form["skills"])
    if form.get("experience"):
        parts.append("EXPERIENCE\n" + form["experience"])
    return "\n".join(parts)


def create_app():
    app = Flask(__name__)
    app.secret_key = "forgecv-dev"  # overridden via env in production

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/generate")
    def generate():
        f = request.files.get("resume_file")
        source = ""
        if f and f.filename:
            try:
                source = parser.extract_text(f.read(), f.filename)
            except Exception:
                source = ""
        if not source.strip():
            source = _assemble_source(request.form)

        jd = request.form.get("job_description", "")
        job = JobSpec(raw=jd, target_keywords=extract_keywords(jd))

        try:
            # One LLM call parses, rewrites, tailors, and structures the resume.
            resume = groq_client.forge_resume(source, jd)
        except Exception:
            return render_template(
                "index.html",
                error="Could not reach the AI service right now. Check your "
                      "GROQ_API_KEY (console.groq.com) and try again.",
            ), 502

        report = score_struct(resume, job)
        try:
            cover = groq_client.write_cover_letter(
                SimpleNamespace(name=resume.get("name", "")), jd) if jd else ""
        except Exception:
            cover = ""

        _last["resume"] = resume
        return render_template("result.html", report=report, resume=resume,
                               cover=cover,
                               combined=report.combined(config.PARSE_WEIGHT, config.MATCH_WEIGHT))

    @app.post("/parse")
    def parse_upload():
        """Read an uploaded resume and return fields to auto-fill the form."""
        f = request.files.get("resume_file")
        if not f or not f.filename:
            return {"ok": False}, 400
        try:
            text = parser.extract_text(f.read(), f.filename)
            d = groq_client.parse_resume(text)
        except Exception:
            d = {}
        exp_lines = []
        for e in (d.get("experiences") or []):
            head = ", ".join(x for x in [e.get("title", ""), e.get("company", "")] if x)
            if head:
                exp_lines.append(head)
            exp_lines += [b for b in (e.get("bullets") or []) if b]
        return {
            "ok": bool(d.get("name") or d.get("skills") or d.get("experiences")),
            "name": d.get("name", ""),
            "email": d.get("email", ""),
            "phone": d.get("phone", ""),
            "skills": ", ".join(d.get("skills") or []),
            "experience": "\n".join(exp_lines),
        }

    @app.get("/download/<fmt>")
    def download(fmt):
        resume = _last.get("resume")
        if not resume:
            return "No resume generated yet", 404
        if fmt == "pdf":
            return send_file(BytesIO(build_pdf_from_dict(resume)), download_name="resume.pdf",
                             mimetype="application/pdf", as_attachment=True)
        if fmt == "docx":
            return send_file(BytesIO(build_docx_from_dict(resume)), download_name="resume.docx",
                             mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                             as_attachment=True)
        return "Unknown format", 400

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
