from io import BytesIO
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from core.models import ResumeData


def build_pdf(r: ResumeData) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=LETTER,
                            leftMargin=0.7 * inch, rightMargin=0.7 * inch,
                            topMargin=0.6 * inch, bottomMargin=0.6 * inch)
    styles = getSampleStyleSheet()
    h = ParagraphStyle("nm", parent=styles["Title"], fontSize=18, spaceAfter=4)
    sec = ParagraphStyle("sec", parent=styles["Heading2"], fontSize=12,
                         spaceBefore=10, spaceAfter=4)
    body = styles["BodyText"]

    flow = [Paragraph(r.name, h)]
    contact = " | ".join(x for x in [r.email, r.phone, *r.links] if x)
    if contact:
        flow.append(Paragraph(contact, body))

    if r.summary:
        flow += [Paragraph("SUMMARY", sec), Paragraph(r.summary, body)]
    if r.skills:
        flow += [Paragraph("SKILLS", sec), Paragraph(", ".join(r.skills), body)]
    if r.experiences:
        flow.append(Paragraph("EXPERIENCE", sec))
        for e in r.experiences:
            head = ", ".join(x for x in [e.title, e.company] if x)
            flow.append(Paragraph(f"<b>{head}</b> {e.start} - {e.end}".strip(), body))
            for b in e.bullets:
                flow.append(Paragraph(f"&bull; {b}", body))
    if r.educations:
        flow.append(Paragraph("EDUCATION", sec))
        for ed in r.educations:
            flow.append(Paragraph(
                ", ".join(x for x in [ed.degree, ed.institution, ed.year] if x), body))

    flow.append(Spacer(1, 6))
    doc.build(flow)
    return buf.getvalue()
