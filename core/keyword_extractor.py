import re
from collections import Counter

STOPWORDS = {
    "the", "and", "with", "for", "you", "your", "our", "are", "will", "have",
    "this", "that", "from", "they", "their", "who", "what", "but", "not", "all",
    "can", "has", "had", "was", "were", "a", "an", "of", "to", "in", "on", "as",
    "we", "is", "be", "or", "at", "it", "by", "experience", "work", "team",
}

# Curated tech/skill vocabulary boosts recall for common resume terms.
KNOWN_SKILLS = {
    "python", "java", "javascript", "typescript", "flask", "django", "fastapi",
    "react", "node", "sql", "postgresql", "mysql", "mongodb", "docker",
    "kubernetes", "aws", "gcp", "azure", "git", "rest", "api", "html", "css",
    "linux", "pandas", "numpy", "pytorch", "tensorflow", "machine", "learning",
}


def extract_keywords(job_description: str) -> list[tuple[str, int]]:
    if not job_description.strip():
        return []
    tokens = re.findall(r"[a-zA-Z][a-zA-Z+#.]{1,}", job_description.lower())
    counts = Counter()
    for tok in tokens:
        if tok in STOPWORDS or len(tok) < 2:
            continue
        counts[tok] += 1

    # Multi-word phrases (adjacent meaningful tokens). ATS rewards exact phrase
    # matches like "machine learning" or "time series", so surface them as targets.
    phrases = Counter()
    for a, b in zip(tokens, tokens[1:]):
        if a in STOPWORDS or b in STOPWORDS or len(a) < 2 or len(b) < 2:
            continue
        phrases[f"{a} {b}"] += 1

    # Rank: known skills first (by weight), then other frequent terms.
    ranked = sorted(
        counts.items(),
        key=lambda kv: (kv[0] in KNOWN_SKILLS, kv[1]),
        reverse=True,
    )
    phrase_items = sorted(phrases.items(), key=lambda kv: kv[1], reverse=True)[:8]
    return ranked + phrase_items
