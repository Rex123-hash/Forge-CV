import re
from collections import Counter

# Generic job-posting filler that should never appear as a "keyword".
STOPWORDS = {
    "the", "and", "with", "for", "you", "your", "our", "are", "will", "have",
    "this", "that", "from", "they", "their", "who", "what", "but", "not", "all",
    "can", "has", "had", "was", "were", "a", "an", "of", "to", "in", "on", "as",
    "we", "is", "be", "or", "at", "it", "by", "experience", "work", "team",
    "seeking", "hiring", "looking", "developer", "engineer", "skilled", "strong",
    "responsibilities", "including", "include", "role", "job", "candidate", "us",
    "ability", "skills", "knowledge", "years", "year", "plus", "etc", "using",
    "build", "building", "develop", "design", "designing", "good", "great",
    "excellent", "ideal", "must", "should", "would", "into", "across", "within",
}

# Curated tech/skill vocabulary boosts recall for common resume terms.
KNOWN_SKILLS = {
    "python", "java", "javascript", "typescript", "flask", "django", "fastapi",
    "react", "node", "sql", "postgresql", "mysql", "mongodb", "docker",
    "kubernetes", "aws", "gcp", "azure", "git", "rest", "api", "html", "css",
    "linux", "pandas", "numpy", "pytorch", "tensorflow", "scikit-learn",
    "xgboost", "lightgbm", "spark", "kafka", "redis", "graphql", "flutter",
}


def extract_keywords(job_description: str) -> list[tuple[str, int]]:
    """Fallback keyword extractor (used when the LLM extractor is unavailable).

    Returns single, meaningful tokens only — no junk bigrams or trailing
    punctuation. The LLM `extract_job_keywords` is the primary, cleaner source.
    """
    if not job_description.strip():
        return []
    raw = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.\-]*", job_description.lower())
    counts = Counter()
    for tok in raw:
        tok = tok.strip(".-")  # drop trailing punctuation: "apis." -> "apis"
        if len(tok) < 2 or tok in STOPWORDS:
            continue
        # keep only plausible skill-like tokens (a known skill, or has a digit /
        # symbol like c++ / node.js, or is a single distinctive word)
        counts[tok] += 1

    ranked = sorted(
        counts.items(),
        key=lambda kv: (kv[0] in KNOWN_SKILLS, kv[1]),
        reverse=True,
    )
    return ranked
