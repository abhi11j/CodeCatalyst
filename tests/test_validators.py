from Scanner.Routes.validators import validate_scan_payload, map_suggestions


def test_validate_scan_payload_valid():
    data = {"target": "owner/repo", "max_results": 5}
    target, max_results, search_type, ai_key, github_token = validate_scan_payload(data)
    assert target == "owner/repo"
    assert max_results == 5


def test_validate_scan_payload_invalid_max_results():
    data = {"target": "owner/repo", "max_results": 0}
    try:
        validate_scan_payload(data)
        assert False, "Expected ValueError"
    except ValueError:
        assert True


def test_map_suggestions():
    suggestions = [{"title": "A", "detail": "B"}]
    mapped = map_suggestions(suggestions)
    assert mapped[0]["title"] == "A"
    assert mapped[0]["detail"] == "B"
    # ai_instruction should be present (None if not provided)
    assert "ai_instruction" in mapped[0] and mapped[0]["ai_instruction"] is None


def test_map_suggestions_with_ai_instruction():
    suggestions = [{"title": "AI", "detail": "do it", "ai_instruction": "perform ai task"}]
    mapped = map_suggestions(suggestions)
    assert mapped[0]["ai_instruction"] == "perform ai task"
