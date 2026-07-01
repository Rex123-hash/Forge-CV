<div align="center">

# ForgeCV

### Build a resume that beats the bots and lands the interview.

An AI-powered, ATS-optimized resume **and** cover-letter builder. Upload your resume or fill in your details, and get a polished, one-page, recruiter-ready PDF and DOCX with a transparent ATS score.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-forgecv--ai.web.app-e35d4f?style=for-the-badge)](https://forgecv-ai.web.app)

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-Llama%203.3%2070B-f55036)
![Cloud Run](https://img.shields.io/badge/Google%20Cloud%20Run-deployed-4285F4?logo=googlecloud&logoColor=white)
![Tests](https://img.shields.io/badge/tests-35%20passing-2ea44f)

</div>

---

## Overview

ForgeCV turns your raw details — typed in, or read straight from an uploaded resume — into a clean, **one-page, ATS-optimized** resume and a tailored cover letter. It rewrites your content with strong, quantified bullets, tailors it to a job description, scores it against real applicant-tracking-system rules, and exports **PDF and DOCX** with a genuine, selectable text layer.

The score is always computed in Python — never claimed by the AI — so it is honest and reproducible.

## Features

- **Two input modes** — upload an existing resume (PDF/DOCX) to auto-fill the fields, or fill them in manually.
- **One powerful AI pass** — parses, rewrites, tailors, and structures your resume into rich sections: Summary, Skills, Education, Projects, Research, Experience, Achievements.
- **Transparent ATS scoring** — separate **parse-ability** and **job-match** scores, with the exact missing keywords to add.
- **Job tailoring** — paste a job description or pick a sample (AI/ML, Web Dev, Data Science, Software Engineer, Cloud/DevOps); keywords are extracted by the LLM, so they are real skills, not filler.
- **In-format, one-page output** — centered name, ruled headings, right-aligned dates, categorized skills, auto-compacted to fit a single page.
- **Downloads** — résumé and cover letter, each as PDF and DOCX.
- **FAQ page** explaining exactly how the scoring and optimization work.

## How the ATS optimization works

Grounded in current ATS-parsing research, ForgeCV enforces:

| Rule | Why |
|------|-----|
| Single-column layout | Parses ~97% of fields vs ~71% for two-column designs |
| Standard headings and round bullets | Recognized by every parser |
| No tables, columns, graphics, icons, header/footer text | These silently break parsers |
| Exact job keywords in context, acronyms spelled out | e.g. "Machine Learning (ML)" |
| Quantified, action-verb bullets, consistent dates | Lets the ATS compute experience cleanly |
| Real selectable text in PDF and DOCX | Not an image of a resume |

The **job-match** score is phrase-aware and uses an LLM-extracted list of the role's real skills, so the number reflects what a real ATS would see.

## Architecture

Python-first: deterministic Python handles parsing, ATS scoring, and document generation. The Groq LLM is used **only** for language tasks (structuring and rewriting content, extracting job keywords, writing the cover letter).

```
app.py                  Flask routes: index, faq, parse, generate, download
config.py               settings (Groq model, ATS weights)
core/
  models.py             dataclasses (ResumeData, JobSpec, ScoreReport, ...)
  keyword_extractor.py  fallback keyword extraction
  ats_scorer.py         parse-ability + phrase-aware job-match scoring
  parser.py             uploaded PDF/DOCX -> text
  groq_client.py        all LLM calls (forge_resume, extract_job_keywords, cover letter)
  resume_builder.py     section-based DOCX (centered name, ruled headings, tab dates)
  pdf_export.py         section-based PDF, auto-fit to one page
templates/              base, index, result, faq
static/                 css, js, logo + favicons, self-hosted font
tests/                  pytest suite (Groq mocked — runs fully offline)
```

## Run locally

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt        # Windows
# source .venv/bin/activate && pip install -r requirements.txt   # macOS/Linux

export GROQ_API_KEY=your_key_here                     # free key: https://console.groq.com
python app.py
```

Open http://localhost:5000

## Test

All tests run offline — Groq is mocked, no API key needed:

```bash
.venv/Scripts/pytest -q
```

## Deploy (Google Cloud Run)

```bash
gcloud run deploy forgecv \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars GROQ_API_KEY=your_key_here
```

Cloud Run builds the `Dockerfile`, injects `$PORT`, and scales to zero. Keep `GROQ_API_KEY` as a deploy-time secret — never commit it.

## Privacy

Your details are processed only to build your resume during the request and are **not stored** afterwards. Files are generated on the fly and streamed to you.

## Tech stack

Python · Flask · Jinja2 · python-docx · ReportLab · pdfminer.six · Groq (Llama 3.3 70B) · Docker · Google Cloud Run

---

<div align="center">

Built by **Amaan Khan**

</div>
