import os

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

# ATS scoring
PARSE_WEIGHT = 0.5
MATCH_WEIGHT = 0.5
TARGET_SCORE = 99
MAX_RETRIES = 3

MAX_UPLOAD_MB = 5
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
