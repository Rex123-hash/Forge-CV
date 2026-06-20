from unittest.mock import MagicMock
from core.models import ResumeData, Experience
from core import groq_client


def _fake_completion(content: str):
    fake = MagicMock()
    fake.choices = [MagicMock(message=MagicMock(content=content))]
    return fake


def test_rewrite_bullets_calls_llm_and_strips_emojis(monkeypatch):
    client = MagicMock()
    client.chat.completions.create.return_value = _fake_completion(
        "Built a scalable Python REST API serving 1k requests/sec"
    )
    monkeypatch.setattr(groq_client, "_get_client", lambda: client)

    out = groq_client.rewrite_bullets(["made an api"], keywords=["python"])
    assert "Python" in out[0]
    client.chat.completions.create.assert_called_once()


def test_cover_letter_returns_text(monkeypatch):
    client = MagicMock()
    client.chat.completions.create.return_value = _fake_completion("Dear Hiring Manager, ...")
    monkeypatch.setattr(groq_client, "_get_client", lambda: client)

    r = ResumeData(name="Aman", experiences=[Experience(title="Intern")])
    letter = groq_client.write_cover_letter(r, job_description="Python role")
    assert "Dear" in letter
