import re
from io import BytesIO
from core.models import ResumeData

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(\+?\d[\d\s-]{8,}\d)")


def extract_text(file_bytes: bytes, filename: str) -> str:
    name = filename.lower()
    if name.endswith(".pdf"):
        from pdfminer.high_level import extract_text as pdf_extract
        return pdf_extract(BytesIO(file_bytes)) or ""
    if name.endswith(".docx"):
        from docx import Document
        doc = Document(BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs)
    return ""


def parse_text_to_resume(text: str) -> ResumeData:
    r = ResumeData()
    if not text.strip():
        return r
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if lines:
        r.name = lines[0]
    em = EMAIL_RE.search(text)
    if em:
        r.email = em.group(0)
    ph = PHONE_RE.search(text)
    if ph:
        r.phone = ph.group(1).strip()

    # crude section split for SKILLS
    upper = text.upper()
    if "SKILLS" in upper:
        after = text[upper.index("SKILLS") + len("SKILLS"):]
        first_block = after.split("\n\n")[0]
        raw = re.split(r"[,\n]", first_block)
        r.skills = [s.strip() for s in raw if 1 < len(s.strip()) < 30][:15]
    return r
