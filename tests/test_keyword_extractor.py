from core.keyword_extractor import extract_keywords


def test_extracts_known_skills():
    jd = "We need a Python developer with Flask, Docker and REST API experience."
    kws = extract_keywords(jd)
    terms = [t for t, _ in kws]
    assert "python" in terms
    assert "flask" in terms
    assert "docker" in terms


def test_ignores_stopwords_and_ranks_by_frequency():
    jd = "Python python python and the the the with flask"
    kws = dict(extract_keywords(jd))
    assert kws["python"] == 3
    assert "the" not in kws


def test_empty_returns_empty():
    assert extract_keywords("") == []
