from backend.law_processor import split_by_sections


def test_split_by_sections_uses_section_headers():
    text = """Section 1 Short title\nThis is the first provision.\n\nSection 2 Commencement\nThis is the second provision."""
    chunks = split_by_sections(text)
    assert len(chunks) == 2
    assert chunks[0][0] == "Section 1"
    assert "first provision" in chunks[0][1].lower()
    assert chunks[1][0] == "Section 2"


def test_split_by_sections_handles_articles():
    text = """Article 14 Equality before law\nText here.\n\nArticle 15 Prohibition of discrimination\nMore text."""
    chunks = split_by_sections(text)
    assert len(chunks) == 2
    assert chunks[0][0] == "Article 14"
    assert chunks[1][0] == "Article 15"

