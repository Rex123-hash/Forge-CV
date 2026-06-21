<div align="center">

# ForgeCV

### Build a resume that beats the bots and lands the interview.

AI-powered, ATS-optimized resume **and** cover letter builder — upload your resume or fill in your details, get a polished one-page PDF/DOCX with a transparent ATS score.

**Live:** https://forgecv-660425204854.asia-south1.run.app

Python · Flask · Groq (Llama 3.3 70B) · Google Cloud Run

</div>

---

## What it does

ForgeCV turns your raw details — typed in, or read straight from an uploaded resume — into a clean, **one-page, ATS-optimized** resume and a tailored cover letter. It rewrites your content with strong, quantified bullets, tailors it to a job description, scores it against real ATS rules, and exports **PDF and DOCX** with a genuine text layer.

The score is always computed in Python — never claimed by the AI — so it's honest and reproducible.

## Features

- **Two input modes** — upload an existing resume (PDF/DOCX) to auto-fill the fields, or fill them in manually.
- **One powerful AI pass** — parses, rewrites, tailors, and structures your resume into rich sections (Summary, Skills, Education, Projects, Research, Experience, Achievements).
- **Transparent ATS scoring** — separate **parse-ability** and **job-match** scores, with the exact missing keywords to add.
- **Tailoring** — paste a job description or pick a sample chip (AI/ML, Web Dev, Data Science, Software Engineer, Cloud/DevOps).
- **One-page, in-format output** — centered name, ruled headings, right-aligned dates, categorized skills; auto-compacted to fit one page.
- **Downloads** — résumé and cover letter, each as PDF and DOCX.
- **Cover letter** — tailored to the job you provide.

## How the ATS optimization works

Based on current applicant-tracking-system parsing research, ForgeCV enforces:

- **Single-column layout** — parses ~97% of fields vs ~71% for two-column designs.
- **Standard section headings** and standard round bullets.
- **No tables, columns, graphics, icons, or header/footer text** — the things that break parsers.
- **Exact job keywords in context**, with acronyms spelled out (e.g. "Machine Learning (ML)").
- **Quantified, action-verb bullets** and **consistent, parseable dates** (so the ATS can compute tenure).
- **Real selectable text** in both PDF and DOCX.

The **job-match** score is phrase-aware: it checks for the exact multi-word phrases from the job description (e.g. "time-series forecasting"), not just single tokens — so the number reflects what a real ATS would see.

## Architecture

Python-first: deterministic Python does parsing, ATS scoring, and document generation; the Groq LLM is used **only** for language tasks (rewriting and structuring content, writing the cover letter).

```
app.py                  Flask routes (index, faq, parse, generate, download)
config.py               settings (Groq model, ATS weights)
core/
  models.py             dataclasses (ResumeData, JobSpec, ScoreReport, ...)
  keyword_extractor.py  job description -> ranked keywords + phrases
  ats_scorer.py         parse-ability + phrase-aware job-match scoring
  parser.py             uploaded PDF/DOCX -> text
  groq_client.py        all LLM calls (forge_resume, parse_resume, cover letter)
  resume_builder.py     section-based DOCX (centered name, ruled headings, tab-aligned dates)
  pdf_export.py         section-based PDF, auto-fit to one page
templates/              base, index, result, faq
static/                 css, js, logo + favicons, self-hosted font
tests/                  pytest suite (Groq mocked — runs offline)
```

## Run locally (Windows)

```powershell
cd forgecv
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
$env:GROQ_API_KEY = "your_key_here"   # free key at https://console.groq.com
.venv\Scripts\python app.py
```

Open http://localhost:5000  ·  (macOS/Linux: use `.venv/bin/` and `export GROQ_API_KEY=...`)

## Test

All tests run offline — Groq is mocked, no API key needed:

```powershell
.venv\Scripts\pytest -q
```

## Deploy to Google Cloud Run

```bash
gcloud run deploy forgecv \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars GROQ_API_KEY=your_key_here
```

Cloud Run builds the `Dockerfile`, injects `$PORT`, and scales to zero. Keep `GROQ_API_KEY` as a deploy-time env var / secret — never commit it.

## Privacy

Your details are processed only to build your resume during the request and are **not stored** after the page closes. Files are generated on the fly and streamed to you.

---

<div align="center">

Built by **Amaan Khan** · [GitHub](https://github.com/Rex123-hash/Forge-CV)

</div>
