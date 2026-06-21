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


FORGE_SYSTEM = (
    "You are an expert resume writer and ATS specialist. You produce clean, "
    "single-column, ATS-optimized resumes. Rules: plain text only, NO emojis, "
    "no markdown symbols. Use strong action verbs and quantified achievements. "
    "NEVER invent employers, titles, degrees, dates, metrics, or facts that are "
    "not in the source; you may only rephrase, tighten, and reorganize real "
    "content. Output STRICT valid JSON only, no prose around it."
)


def _chat_json(system: str, user: str, attempts: int = 3) -> dict:
    """Call the LLM expecting JSON, with retries for transient failures."""
    last = None
    for _ in range(attempts):
        try:
            resp = _get_client().chat.completions.create(
                model=config.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            return json.loads(_strip(resp.choices[0].message.content))
        except Exception as e:  # transient network / rate / parse error
            last = e
    raise RuntimeError(f"Groq JSON call failed after {attempts} attempts: {last}")


def forge_resume(source_text: str, job_description: str = "") -> dict:
    """Turn raw source (uploaded resume text or assembled form fields) into a
    fully structured, rewritten, ATS-optimized resume as a section-based dict.

    Returns: {name, contact, sections: [{heading, body?, entries?:[
              {header, subheader, date, bullets[]}]}]}
    """
    tailored = bool(job_description.strip())
    user = (
        "Build a professional, ATS-optimized resume as JSON from the SOURCE"
        + (", tailored to the TARGET JOB (weave in its keywords truthfully)" if tailored else "")
        + ". Use this exact schema:\n"
        '{"name": "Full Name",'
        ' "contact": "phone | email | linkedin | github (one line)",'
        ' "sections": ['
        '   {"heading": "SUMMARY", "body": "2-3 sentence paragraph"},'
        '   {"heading": "TECHNICAL SKILLS", "body": "Category: items, one category per line"},'
        '   {"heading": "EDUCATION", "entries": [{"header": "Institution", "subheader": "Degree, GPA", "date": "dates", "bullets": []}]},'
        '   {"heading": "PROJECTS", "entries": [{"header": "Name | tech stack", "subheader": "link / context", "date": "year", "bullets": ["..."]}]},'
        '   {"heading": "WORK EXPERIENCE", "entries": [{"header": "Role", "subheader": "Company", "date": "dates", "bullets": ["..."]}]},'
        '   {"heading": "RESEARCH"/"ACHIEVEMENTS"/etc, "entries": [...]}'
        ' ]}\n'
        "Keep EVERY real section present in the source (summary, education, skills, "
        "research, projects, work experience, achievements/certifications). Preserve "
        "real numbers, dates, links, and tech stacks. Strengthen bullet wording. "
        "Skills go in 'body' with category lines; other sections use 'entries'.\n"
        "IMPORTANT - the resume MUST fit on ONE page: summary max 2 sentences; at "
        "most 2 bullets per project/experience entry; each bullet max ~22 words; keep "
        "only the most relevant/impressive content; education and achievements stay "
        "concise. Do not pad.\n\n"
        + (f"TARGET JOB:\n{job_description.strip()}\n\n" if tailored else "")
        + f"SOURCE:\n{source_text[:9000]}"
    )
    return _chat_json(FORGE_SYSTEM, user)


def write_cover_letter(resume, job_description: str) -> str:
    prompt = (
        f"Write a concise, professional cover letter (max 250 words) for "
        f"{resume.name or 'the candidate'} applying to this job:\n"
        f"{job_description}\n\nKeep it plain text, no emojis."
    )
    return _chat(prompt)
