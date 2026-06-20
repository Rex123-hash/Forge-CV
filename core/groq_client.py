import re
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


def write_cover_letter(resume, job_description: str) -> str:
    prompt = (
        f"Write a concise, professional cover letter (max 250 words) for "
        f"{resume.name or 'the candidate'} applying to this job:\n"
        f"{job_description}\n\nKeep it plain text, no emojis."
    )
    return _chat(prompt)
