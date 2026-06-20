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

    r.skills = _extract_skills(text)
    return r


# Headings that mark the end of the SKILLS block.
SECTION_HEADERS = {
    "EXPERIENCE", "EDUCATION", "PROJECTS", "SUMMARY", "WORK", "CONTACT",
    "CERTIFICATIONS", "ACHIEVEMENTS", "AWARDS", "INTERESTS", "OBJECTIVE",
    "PROFILE", "LANGUAGES", "REFERENCES",
}


def _is_section_header(line: str) -> bool:
    alpha = "".join(ch for ch in line if ch.isalpha() or ch.isspace()).strip()
    return alpha.upper() in SECTION_HEADERS


def _extract_skills(text: str) -> list[str]:
    """Collect skill items listed after a SKILLS heading, stopping at the
    next section header so we don't swallow EXPERIENCE/EDUCATION content."""
    lines = text.splitlines()
    start = None
    # Prefer a line that is exactly the SKILLS heading.
    for i, ln in enumerate(lines):
        if ln.strip().upper() == "SKILLS":
            start = i + 1
            break
    # Fall back to the first line that mentions SKILLS inline.
    if start is None:
        for i, ln in enumerate(lines):
            if "SKILLS" in ln.upper():
                start = i + 1
                break
    if start is None:
        return []

    collected = []
    for ln in lines[start:]:
        if not ln.strip():
            continue
        if _is_section_header(ln):
            break
        collected.append(ln)

    raw = re.split(r"[,\n]", "\n".join(collected))
    skills = []
    for item in raw:
        item = item.lstrip("-•* ").strip()
        if 1 < len(item) < 30 and not _is_section_header(item):
            skills.append(item)
    return skills[:15]
