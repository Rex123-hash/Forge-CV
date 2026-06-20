from flask import Flask, render_template, request, session, send_file
from io import BytesIO
import config
from core.models import ResumeData, Experience, JobSpec
from core.keyword_extractor import extract_keywords
from core import generator, parser, groq_client
from core.resume_builder import build_docx
from core.pdf_export import build_pdf

_last = {}  # in-memory last result for downloads (stateless per process)


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

        resume, report = generator.generate(resume, job)
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
