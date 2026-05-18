from backend.query import understand_query


def test_query_detects_section_only():
    intent = understand_query("What does Section 302 say?")
    assert intent.needs_section is True
    assert intent.needs_case is False


def test_query_detects_case_only():
    intent = understand_query("Find a case on bail in the Supreme Court")
    assert intent.needs_section is True
    assert intent.needs_case is True

