import re
import json
import config

_client = None

SYSTEM_RULES = (
    "You are a professional resume writer. Rules: write concise, quantified, "
    "action-verb bullet points. Use ONLY plain text. Never use emojis, markdown "
    "symbols, or decorative characters. Never invent jobs, employers, degrees, "
    "or credentials the user did not provide; you may only rephrase real "
    "experience and naturally include relevant keywords."
)

EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F0FF]",
    flags=re.UNICODE,
)


def _strip(text: str) -> str:
    return EMOJI_RE.sub("", text).strip()


def _get_client():
    global _client
    if _client is None:
        from groq import Groq
        _client = Groq(api_key=config.GROQ_API_KEY)
    return _client


def _chat(prompt: str) -> str:
    resp = _get_client().chat.completions.create(
        model=config.GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_RULES},
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
    )
    return _strip(resp.choices[0].message.content)


def rewrite_bullets(bullets: list[str], keywords: list[str]) -> list[str]:
    if not bullets:
        return []
    kw = ", ".join(keywords)
    prompt = (
        f"Rewrite each resume bullet to be strong and quantified. Naturally "
        f"include these keywords where truthful: {kw}.\n"
        f"Return one rewritten bullet per line, no numbering.\n\n"
        + "\n".join(f"- {b}" for b in bullets)
    )
    out = _chat(prompt)
    return [ln.lstrip("-• ").strip() for ln in out.splitlines() if ln.strip()]


def parse_resume(raw_text: str) -> dict:
    """Use the LLM to turn raw resume text into structured fields.

    Returns a dict with keys: name, email, phone, links, summary, skills,
    experiences (list of {title, company, start, end, bullets}), educations
    (list of {degree, institution, year}). Returns {} on failure so the caller
    can fall back to the regex parser.
    """
    if not raw_text.strip():
        return {}
    prompt = (
        "Extract structured data from this resume. Return STRICT JSON with keys: "
        "name (string), email (string), phone (string), links (list of strings), "
        "summary (string), skills (list of strings), experiences (list of objects "
        "with title, company, start, end, bullets[list of strings]), educations "
        "(list of objects with degree, institution, year). Use empty string/list "
        "when a field is absent. Do NOT invent anything. name must be the person's "
        "name only, never their contact line.\n\nRESUME:\n" + raw_text[:7000]
    )
    try:
        resp = _get_client().chat.completions.create(
            model=config.GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You extract resume data as strict "
                 "JSON. Output only JSON, no prose, no emojis."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        return json.loads(_strip(resp.choices[0].message.content))
    except Exception:
        return {}


def write_cover_letter(resume, job_description: str) -> str:
    prompt = (
        f"Write a concise, professional cover letter (max 250 words) for "
        f"{resume.name or 'the candidate'} applying to this job:\n"
        f"{job_description}\n\nKeep it plain text, no emojis."
    )
    return _chat(prompt)
