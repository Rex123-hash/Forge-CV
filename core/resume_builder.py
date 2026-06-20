from io import BytesIO
from docx import Document
from docx.shared import Pt
from core.models import ResumeData


def build_docx(r: ResumeData) -> bytes:
    """Single-column, standard-heading, table-free DOCX (ATS-safe)."""
    doc = Document()

    name = doc.add_paragraph()
    run = name.add_run(r.name)
    run.bold = True
    run.font.size = Pt(18)

    contact = " | ".join(x for x in [r.email, r.phone, *r.links] if x)
    if contact:
        doc.add_paragraph(contact)

    if r.summary:
        doc.add_heading("SUMMARY", level=1)
        doc.add_paragraph(r.summary)

    if r.skills:
        doc.add_heading("SKILLS", level=1)
        doc.add_paragraph(", ".join(r.skills))

    if r.experiences:
        doc.add_heading("EXPERIENCE", level=1)
        for e in r.experiences:
            head = ", ".join(x for x in [e.title, e.company] if x)
            dates = f"{e.start} - {e.end}".strip(" -")
            doc.add_paragraph(f"{head}  {dates}".strip())
            for b in e.bullets:
                doc.add_paragraph(b, style="List Bullet")

    if r.educations:
        doc.add_heading("EDUCATION", level=1)
        for ed in r.educations:
            line = ", ".join(x for x in [ed.degree, ed.institution, ed.year] if x)
            doc.add_paragraph(line)

    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()
