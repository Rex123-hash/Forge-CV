import re
import json
import config

_client = None

SYSTEM_RULES = (
    "You are a professional resume writer. Rules: write concise, quantified, "
    "action-verb bullet points. Use ONLY plain text. Never use emojis, markdown "
    "symbols, or decorative characters. Use flawless spelling and grammar - "
    "proofread every word and correct any typos. Never invent jobs, employers, "
    "degrees, or credentials the user did not provide; you may only rephrase real "
    "experience and naturally include relevant keywords."
)

EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F0FF]",
    flags=re.UNICODE,
)


def _strip(text: str) -> str:
    """Remove emojis only. Em dashes (asides) and en dashes (ranges) are kept,
    per the resume spec."""
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
        temperature=0.3,
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
    "Use FLAWLESS spelling and grammar - proofread every word; correct any typos "
    "from the source; use standard US English; keep technical terms, product "
    "names and acronyms spelled correctly. "
    "NEVER invent employers, titles, degrees, dates, metrics, or facts that are "
    "not in the source; you may only rephrase, tighten, and reorganize real "
    "content. Output STRICT valid JSON only, no prose around it."
)


def _chat_json(system: str, user: str, attempts: int = 3, temperature: float = 0.2) -> dict:
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
                temperature=temperature,
                response_format={"type": "json_object"},
            )
            return json.loads(_strip(resp.choices[0].message.content))
        except Exception as e:  # transient network / rate / parse error
            last = e
    raise RuntimeError(f"Groq JSON call failed after {attempts} attempts: {last}")


def extract_job_keywords(job_description: str) -> list[str]:
    """Extract the real, concrete skills/keywords a resume should match for this
    job — clean and properly cased (e.g. 'React', 'REST APIs', 'Machine Learning'),
    NOT filler words like 'seeking' or 'developer'. Returns [] on failure."""
    if not job_description.strip():
        return []
    user = (
        "From this job description, list the key hard skills, tools, technologies "
        "and concrete competencies a candidate's resume should match. Return STRICT "
        'JSON {"keywords": ["..."]} with 8-14 items. Each item must be a real, '
        "specific skill or technology, properly capitalized and deduplicated. Do NOT "
        "include filler words (seeking, hiring, looking, developer, engineer, "
        "experience, strong, responsibilities) or vague phrases.\n\n"
        + job_description[:4000]
    )
    try:
        d = _chat_json(
            "You extract concrete resume keywords as strict JSON. Output only JSON.",
            user)
        out, seen = [], set()
        for k in (d.get("keywords") or []):
            k = str(k).strip()
            if k and 1 < len(k) < 40 and k.lower() not in seen:
                seen.add(k.lower())
                out.append(k)
        return out[:14]
    except Exception:
        return []


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
        "Keep EVERY real section present in the source. Preserve real numbers, dates, "
        "links, and tech stacks. Strengthen wording. Skills go in 'body' (category "
        "lines); other sections use 'entries'.\n"
        "SECTION ORDER (top to bottom): SUMMARY, EDUCATION, TECHNICAL SKILLS, "
        "RESEARCH (only if there is a paper - place it above projects for ML/research "
        "roles), RELEVANT PROJECTS, WORK EXPERIENCE, NOTABLE ACHIEVEMENTS & "
        "CERTIFICATIONS. Use these exact heading names. Omit a section only if the "
        "source has nothing for it.\n"
        "SUMMARY: 3-4 lines. Formula: who you are -> what you have done -> what you are "
        "skilled in -> what you are seeking. Mirror the target job's language. No "
        "'passionate hardworking individual' filler.\n"
        "TECHNICAL SKILLS: 4-5 labeled rows (one per line as 'Label: items'), NOT one "
        "long list. Order the rows by relevance to the target job (most-wanted category "
        "first). Give full term AND acronym, e.g. 'Building Information Modeling (BIM)'. "
        "Only skills supported by the source.\n"
        "RELEVANT PROJECTS: header = 'Project Name | Tech, Stack' (real stack); "
        "subheader = the project link plus context (e.g. 'github.com/... · Hackathon'); "
        "date = year. 2-3 bullets each, strongest project first. Bullet formula: action "
        "verb + impact + what it is + how. Consistent voice (all start with a verb).\n"
        "WORK EXPERIENCE: header = role; subheader = 'Company · duration' (italic); "
        "date = 'Mon YYYY – Mon YYYY' (en dash). Quantified bullets.\n"
        "NOTABLE ACHIEVEMENTS & CERTIFICATIONS: one bullet each, most impressive first, "
        "formatted 'Award/title — specific detail' (space, em dash —, space, then detail).\n"
        "IMPORTANT: the resume MUST fit ONE page: summary 3-4 lines; at most 2-3 "
        "bullets per project, 1-2 per job; each bullet max ~24 words; keep only the most "
        "relevant content. Do not pad.\n"
        "RULES (follow strictly):\n"
        "- Reverse-chronological order. Date ranges use an en dash: 'Jun 2025 – Aug 2025'.\n"
        "- Reuse the EXACT keywords/phrases from the target job where they truthfully apply.\n"
        "- HONESTY: never claim a selection, result, or metric you cannot support from the "
        "source; never fabricate numbers; 'submitted' is not 'accepted' is not 'published'; "
        "state co-author vs primary author accurately.\n"
        "- Flawless spelling and grammar (US English). Plain text, no emojis, no markdown, "
        "round bullets only.\n\n"
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
