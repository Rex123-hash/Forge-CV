import os
import re
from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, HRFlowable)
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from core.models import ResumeData

_RULE = colors.HexColor("#9a917c")
_GREY = colors.HexColor("#444444")
_LINK_HEX = "#1155CC"
_AVAIL = LETTER[0] - 0.8 * inch  # 0.4in margins each side
_FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "fonts")

# Color github/linkedin and any http(s) or domain/path link blue (not emails).
_URL_RE = re.compile(
    r"(https?://\S+|(?:www\.)?(?:github|linkedin)\.com/\S+|\b[\w-]+\.(?:com|io|app|dev|org|net|ai|co)/\S+)",
    re.I)

_fonts_ready = None


def _font_set():
    """Register Carlito (metric-compatible with Calibri) once; fall back to
    Helvetica if the TTFs are unavailable. Returns (regular, bold, italic)."""
    global _fonts_ready
    if _fonts_ready is None:
        try:
            pdfmetrics.registerFont(TTFont("Calibri", os.path.join(_FONT_DIR, "Carlito-Regular.ttf")))
            pdfmetrics.registerFont(TTFont("Calibri-Bold", os.path.join(_FONT_DIR, "Carlito-Bold.ttf")))
            pdfmetrics.registerFont(TTFont("Calibri-Italic", os.path.join(_FONT_DIR, "Carlito-Italic.ttf")))
            pdfmetrics.registerFont(TTFont("Calibri-BoldItalic", os.path.join(_FONT_DIR, "Carlito-BoldItalic.ttf")))
            registerFontFamily("Calibri", normal="Calibri", bold="Calibri-Bold",
                               italic="Calibri-Italic", boldItalic="Calibri-BoldItalic")
            _fonts_ready = ("Calibri", "Calibri-Bold", "Calibri-Italic")
        except Exception:
            _fonts_ready = ("Helvetica", "Helvetica-Bold", "Helvetica-Oblique")
    return _fonts_ready


def _linkify(line: str) -> str:
    """Escape a line and color any link tokens blue (#1155CC)."""
    esc = escape(line)
    return _URL_RE.sub(lambda m: f'<font color="{_LINK_HEX}">{m.group(0)}</font>', esc)


def _bold_category(line: str) -> str:
    """'Languages: Python, SQL' -> '<b>Languages:</b> Python, SQL'."""
    if ":" in line:
        head, rest = line.split(":", 1)
        return f"<b>{escape(head)}:</b>{escape(rest)}"
    return escape(line)


def _bullet(b: str, bold_lead: bool) -> str:
    """Render a bullet; for achievements bold the label before the em dash."""
    if bold_lead and " — " in b:
        lead, rest = b.split(" — ", 1)
        return f"&bull;&nbsp;<b>{escape(lead)}</b> — {escape(rest)}"
    return "&bull;&nbsp;" + escape(b)


def _render_pdf(d: dict, k: float) -> bytes:
    """Render the resume at scale k (fonts/spacing) for one-page fitting."""
    reg, bold, ital = _font_set()
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=LETTER, leftMargin=0.45 * inch,
                            rightMargin=0.45 * inch, topMargin=0.4 * inch,
                            bottomMargin=0.35 * inch, title=d.get("name", "Resume"))
    base = getSampleStyleSheet()["BodyText"]
    base.fontName = reg
    name_s = ParagraphStyle("nm", parent=base, fontName=bold,
                            fontSize=22 * k, leading=25 * k, alignment=TA_CENTER, spaceAfter=2 * k)
    contact_s = ParagraphStyle("ct", parent=base, fontName=reg, fontSize=9 * k, leading=11.5 * k,
                               alignment=TA_CENTER, textColor=_GREY, spaceAfter=4 * k)
    sec_s = ParagraphStyle("sec", parent=base, fontName=bold,
                           fontSize=10.5 * k, leading=12 * k, spaceBefore=8 * k, spaceAfter=0)
    left_s = ParagraphStyle("lf", parent=base, fontName=bold,
                            fontSize=10 * k, leading=12 * k)
    date_s = ParagraphStyle("dt", parent=base, fontName=reg, fontSize=8.6 * k, leading=12 * k,
                            alignment=TA_RIGHT, textColor=_GREY)
    sub_s = ParagraphStyle("sub", parent=base, fontName=ital,
                           fontSize=9 * k, leading=11 * k, textColor=_GREY, spaceAfter=1 * k)
    bullet_s = ParagraphStyle("bu", parent=base, fontName=reg, fontSize=9.5 * k, leading=11.5 * k,
                              leftIndent=11 * k, firstLineIndent=-7 * k, spaceAfter=1 * k)
    body_s = ParagraphStyle("bd", parent=base, fontName=reg, fontSize=9.5 * k, leading=12 * k, spaceAfter=0.5 * k)

    flow = [Paragraph(escape(d.get("name", "")), name_s)]
    if d.get("contact"):
        flow.append(Paragraph(_linkify(d["contact"]), contact_s))

    for s in d.get("sections", []) or []:
        heading = (s.get("heading") or "").upper()
        is_award = ("ACHIEVEMENT" in heading or "CERTIFICATION" in heading
                    or "AWARD" in heading)
        if heading:
            flow.append(Paragraph(escape(heading), sec_s))
            flow.append(HRFlowable(width="100%", thickness=0.6, color=_RULE,
                                   spaceBefore=1 * k, spaceAfter=3 * k))
        if s.get("body"):
            for line in str(s["body"]).split("\n"):
                if line.strip():
                    flow.append(Paragraph(_bold_category(line.strip()), body_s))
        for e in s.get("entries", []) or []:
            header, date = e.get("header", ""), e.get("date", "")
            if header or date:
                row = [[Paragraph(escape(header), left_s),
                        Paragraph(escape(date), date_s)]]
                t = Table(row, colWidths=[_AVAIL * 0.76, _AVAIL * 0.24])
                t.setStyle(TableStyle([
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 3 * k),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]))
                flow.append(t)
            if e.get("subheader"):
                flow.append(Paragraph(_linkify(e["subheader"]), sub_s))
            for b in e.get("bullets", []) or []:
                if b:
                    flow.append(Paragraph(_bullet(b, is_award), bullet_s))

    doc.build(flow)
    return buf.getvalue()


def build_cover_pdf(name: str, text: str) -> bytes:
    """Render a cover letter to a clean, ATS-safe PDF (real text layer)."""
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=LETTER, leftMargin=inch, rightMargin=inch,
                            topMargin=0.9 * inch, bottomMargin=0.9 * inch,
                            title=(name or "Cover letter"))
    styles = getSampleStyleSheet()
    nm = ParagraphStyle("cn", parent=styles["Title"], fontSize=15, alignment=0, spaceAfter=12)
    body = ParagraphStyle("cb", parent=styles["BodyText"], fontSize=10.5, leading=15, spaceAfter=9)
    flow = []
    if name:
        flow.append(Paragraph(escape(name), nm))
    for para in text.split("\n\n"):
        para = para.strip()
        if para:
            flow.append(Paragraph(escape(para).replace("\n", "<br/>"), body))
    doc.build(flow)
    return buf.getvalue()


def _page_count(data: bytes) -> int:
    from pdfminer.pdfparser import PDFParser
    from pdfminer.pdfdocument import PDFDocument
    from pdfminer.pdfpage import PDFPage
    document = PDFDocument(PDFParser(BytesIO(data)))
    return sum(1 for _ in PDFPage.create_pages(document))


def build_pdf_from_dict(d: dict) -> bytes:
    """Render to an ATS-safe PDF that matches the target layout and fits ONE
    page (progressively compacts font/spacing until it fits)."""
    data = None
    for k in (1.0, 0.95, 0.9, 0.86, 0.82, 0.78, 0.74):
        data = _render_pdf(d, k)
        if _page_count(data) <= 1:
            return data
    return data


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
