# ForgeCV

AI-powered, ATS-optimized resume and cover letter builder.

Turn your details (typed or parsed from an uploaded resume) into a clean,
ATS-friendly resume and a tailored cover letter — with two transparent scores
(parse-ability + job-match) that the app regenerates toward 99+. Built
Python-first; the Groq LLM is used only for language rewriting.

## Tech stack

- **Backend / logic:** Python 3.11, Flask
- **AI:** Groq (Llama 3.3 70B) — only for rewriting bullets and the cover letter
- **Documents:** python-docx (DOCX), reportlab (PDF, real text layer)
- **Parsing:** pdfminer.six (PDF), python-docx (DOCX)
- **UI:** Jinja2 templates + hand-written CSS (warm paper + coral, Plus Jakarta Sans)
- **Deploy:** Docker → Google Cloud Run

The ATS score is always computed by Python (`core/ats_scorer.py`), never claimed
by the LLM.

## Run locally (Windows)

```powershell
cd forgecv
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
$env:GROQ_API_KEY = "your_key_here"   # get a free key at https://console.groq.com
.venv\Scripts\python app.py
```

Open http://localhost:5000

(macOS/Linux: use `.venv/bin/` instead of `.venv\Scripts\`, and
`export GROQ_API_KEY=...`.)

## Test

All tests run offline (Groq is mocked) — no API key needed:

```powershell
.venv\Scripts\pytest -q
```

## Regenerate favicons (optional)

Favicons are pre-generated and committed. To rebuild them from
`static/img/logo.svg`:

```powershell
.venv\Scripts\python scripts\gen_favicons.py
```

## Deploy to Google Cloud Run

```bash
gcloud run deploy forgecv \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars GROQ_API_KEY=your_key_here
```

Cloud Run builds the `Dockerfile`, injects `$PORT`, and scales to zero. Keep
`GROQ_API_KEY` as a deploy-time env var / secret — never commit it.

## Project layout

```
app.py              Flask routes (index / generate / download)
config.py           settings (Groq model, ATS weights, retry budget)
core/
  models.py         dataclasses (ResumeData, JobSpec, ScoreReport, ...)
  keyword_extractor.py  job description -> ranked keywords
  ats_scorer.py     parse-ability + job-match scoring
  parser.py         uploaded PDF/DOCX -> ResumeData
  groq_client.py    all LLM calls (emoji-stripped)
  generator.py      generate -> score -> retry loop (99+)
  resume_builder.py ATS-clean DOCX
  pdf_export.py     ATS-safe PDF (real text layer)
templates/          base, index, result
static/             css, js, img/logo.svg, favicons, fonts
tests/              pytest suite (Groq mocked)
```
