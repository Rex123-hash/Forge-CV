from io import BytesIO
from pdfminer.high_level import extract_text
from core.models import ResumeData, Experience
from core.pdf_export import build_pdf


def test_pdf_has_selectable_text():
    r = ResumeData(name="Aman K", email="a@x.com", phone="+91 9999999999",
                   skills=["Python"],
                   experiences=[Experience(title="Intern", bullets=["Built API"])])
    data = build_pdf(r)
    assert data[:4] == b"%PDF"
    text = extract_text(BytesIO(data))
    assert "Aman K" in text          # real text layer, not an image
    assert "Built API" in text
