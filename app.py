import json
from io import BytesIO
from types import SimpleNamespace
from flask import Flask, render_template, request, send_file
import config
from core.models import JobSpec
from core.keyword_extractor import extract_keywords
from core import parser, groq_client
from core.ats_scorer import score_struct
from core.resume_builder import build_docx_from_dict, build_cover_docx
from core.pdf_export import build_pdf_from_dict, build_cover_pdf

_DOCX_MIME = ("application/vnd.openxmlformats-officedocument"
              ".wordprocessingml.document")


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

    @app.get("/faq")
    def faq():
        return render_template("faq.html")

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
        keywords = []
        if jd.strip():
            keywords = groq_client.extract_job_keywords(jd)  # clean, real skills
            if not keywords:  # fallback if the LLM call is unavailable
                keywords = [t for t, _ in extract_keywords(jd)][:14]
        job = JobSpec(raw=jd, target_keywords=[(k, 1) for k in keywords])

        try:
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

        # Stateless: the result page carries the data so downloads work on any
        # server worker/instance (no shared in-memory state needed).
        return render_template("result.html", report=report, resume=resume,
                               resume_json=json.dumps(resume), cover=cover,
                               combined=report.combined(config.PARSE_WEIGHT,
                                                        config.MATCH_WEIGHT))

    @app.post("/download/<doc>/<fmt>")
    def download(doc, fmt):
        if doc == "resume":
            try:
                resume = json.loads(request.form.get("resume", "{}"))
            except Exception:
                resume = {}
            if not resume:
                return "Nothing to download — generate a resume first.", 400
            if fmt == "pdf":
                return send_file(BytesIO(build_pdf_from_dict(resume)),
                                 download_name="resume.pdf",
                                 mimetype="application/pdf", as_attachment=True)
            if fmt == "docx":
                return send_file(BytesIO(build_docx_from_dict(resume)),
                                 download_name="resume.docx",
                                 mimetype=_DOCX_MIME, as_attachment=True)
        elif doc == "cover":
            name = request.form.get("name", "")
            text = request.form.get("cover", "")
            if not text.strip():
                return "No cover letter to download.", 400
            if fmt == "pdf":
                return send_file(BytesIO(build_cover_pdf(name, text)),
                                 download_name="cover-letter.pdf",
                                 mimetype="application/pdf", as_attachment=True)
            if fmt == "docx":
                return send_file(BytesIO(build_cover_docx(name, text)),
                                 download_name="cover-letter.docx",
                                 mimetype=_DOCX_MIME, as_attachment=True)
        return "Unknown download.", 400

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
