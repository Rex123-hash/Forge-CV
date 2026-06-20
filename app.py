from flask import Flask, render_template, request, session, send_file
from io import BytesIO
import config
from core.models import ResumeData, Experience, Education, JobSpec
from core.keyword_extractor import extract_keywords
from core import generator, parser, groq_client
from core.resume_builder import build_docx
from core.pdf_export import build_pdf

_last = {}  # in-memory last result for downloads (stateless per process)


def _resume_from_dict(d: dict) -> ResumeData:
    """Build a ResumeData from the LLM-parsed resume dict."""
    exps = [
        Experience(title=e.get("title", ""), company=e.get("company", ""),
                   start=str(e.get("start", "")), end=str(e.get("end", "")),
                   bullets=[b for b in (e.get("bullets") or []) if b])
        for e in (d.get("experiences") or [])
    ]
    eds = [
        Education(degree=e.get("degree", ""), institution=e.get("institution", ""),
                  year=str(e.get("year", "")))
        for e in (d.get("educations") or [])
    ]
    return ResumeData(
        name=d.get("name", ""), email=d.get("email", ""), phone=d.get("phone", ""),
        links=[l for l in (d.get("links") or []) if l], summary=d.get("summary", ""),
        skills=[s for s in (d.get("skills") or []) if s],
        experiences=exps, educations=eds,
        projects=[p for p in (d.get("projects") or []) if p],
    )


def create_app():
    app = Flask(__name__)
    app.secret_key = "forgecv-dev"  # overridden via env in production

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/generate")
    def generate():
        f = request.files.get("resume_file")
        if f and f.filename:
            text = parser.extract_text(f.read(), f.filename)
            data = groq_client.parse_resume(text)
            # LLM parse preferred; fall back to regex if it yields nothing usable.
            if data and (data.get("name") or data.get("experiences") or data.get("skills")):
                resume = _resume_from_dict(data)
            else:
                resume = parser.parse_text_to_resume(text)
        else:
            resume = ResumeData(
                name=request.form.get("name", ""),
                email=request.form.get("email", ""),
                phone=request.form.get("phone", ""),
                skills=[s.strip() for s in request.form.get("skills", "").split(",") if s.strip()],
                experiences=[Experience(bullets=[request.form.get("experience", "")])],
            )
        jd = request.form.get("job_description", "")
        job = JobSpec(raw=jd, target_keywords=extract_keywords(jd))

        try:
            resume, report = generator.generate(resume, job)
        except Exception:
            # The only network dependency is Groq; a missing/invalid key or an
            # outage lands here. Show a friendly message instead of a 500.
            return render_template(
                "index.html",
                error="Could not reach the AI service. Set GROQ_API_KEY to a "
                      "valid key from console.groq.com and try again.",
            ), 502

        try:
            cover = groq_client.write_cover_letter(resume, jd) if jd else ""
        except Exception:
            cover = ""

        _last["resume"] = resume
        return render_template("result.html", report=report, resume=resume,
                               cover=cover,
                               combined=report.combined(config.PARSE_WEIGHT, config.MATCH_WEIGHT))

    @app.get("/download/<fmt>")
    def download(fmt):
        resume = _last.get("resume")
        if not resume:
            return "No resume generated yet", 404
        if fmt == "pdf":
            return send_file(BytesIO(build_pdf(resume)), download_name="resume.pdf",
                             mimetype="application/pdf", as_attachment=True)
        if fmt == "docx":
            return send_file(BytesIO(build_docx(resume)), download_name="resume.docx",
                             mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                             as_attachment=True)
        return "Unknown format", 400

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
