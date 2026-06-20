from core.parser import parse_text_to_resume


def test_parses_contact_and_skills_from_text():
    text = (
        "Aman Kumar\n"
        "Email: aman@example.com  Phone: +91 9876543210\n"
        "SKILLS\nPython, Flask, Docker, SQL\n"
        "EXPERIENCE\nSoftware Intern at Acme (2024-2025)\n"
        "- Built a REST API\n"
    )
    r = parse_text_to_resume(text)
    assert r.email == "aman@example.com"
    assert "Python" in r.skills or "python" in [s.lower() for s in r.skills]
    assert r.phone.replace(" ", "").endswith("9876543210")


def test_empty_text_returns_empty_resume():
    r = parse_text_to_resume("")
    assert r.name == ""
    assert r.skills == []
