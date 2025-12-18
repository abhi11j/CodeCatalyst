from Scanner.GitHub.AI.response_parser import extract_suggestions_from_response


def test_extract_suggestions_from_response():
    outer = {
        "choices": [
            {
                "message": {
                    "content": '{"suggestions": [{"title": "Add README", "detail": "Add README.md", "importance": 8}]}'
                }
            }
        ]
    }
    import json
    raw = json.dumps(outer)
    suggestions = extract_suggestions_from_response(raw)
    assert isinstance(suggestions, list)
    assert suggestions[0]["title"] == "Add README"
