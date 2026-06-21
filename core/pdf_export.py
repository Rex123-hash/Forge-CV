from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from core.models import ResumeData


def build_pdf_from_dict(d: dict) -> bytes:
    """Render a section-based resume dict to an ATS-safe PDF (real text layer)."""
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=LETTER,
                            leftMargin=0.7 * inch, rightMargin=0.7 * inch,
                            topMargin=0.55 * inch, bottomMargin=0.55 * inch)
    styles = getSampleStyleSheet()
    name_s = ParagraphStyle("nm", parent=styles["Title"], fontSize=17, spaceAfter=2, alignment=0)
    contact_s = ParagraphStyle("ct", parent=styles["BodyText"], fontSize=9.5, textColor="#555555", spaceAfter=6)
    sec_s = ParagraphStyle("sec", parent=styles["Heading2"], fontSize=11.5, spaceBefore=10, spaceAfter=3, textColor="#1c1a16")
    entry_s = ParagraphStyle("en", parent=styles["BodyText"], fontSize=10.5, spaceBefore=4, spaceAfter=0)
    sub_s = ParagraphStyle("sub", parent=styles["BodyText"], fontSize=9.5, textColor="#555555", spaceAfter=1)
    bullet_s = ParagraphStyle("bu", parent=styles["BodyText"], fontSize=10, leftIndent=12, spaceAfter=1)
    body_s = ParagraphStyle("bd", parent=styles["BodyText"], fontSize=10, spaceAfter=1)

    flow = [Paragraph(escape(d.get("name", "")), name_s)]
    if d.get("contact"):
        flow.append(Paragraph(escape(d["contact"]), contact_s))

    for s in d.get("sections", []) or []:
        if s.get("heading"):
            flow.append(Paragraph(escape(s["heading"].upper()), sec_s))
        if s.get("body"):
            for line in str(s["body"]).split("\n"):
                if line.strip():
                    flow.append(Paragraph(escape(line.strip()), body_s))
        for e in s.get("entries", []) or []:
            header = e.get("header", "")
            date = e.get("date", "")
            if header or date:
                top = f"<b>{escape(header)}</b>" + (f"  {escape(date)}" if date else "")
                flow.append(Paragraph(top, entry_s))
            if e.get("subheader"):
                flow.append(Paragraph(escape(e["subheader"]), sub_s))
            for b in e.get("bullets", []) or []:
                if b:
                    flow.append(Paragraph("&bull; " + escape(b), bullet_s))

    flow.append(Spacer(1, 6))
    doc.build(flow)
    return buf.getvalue()


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
