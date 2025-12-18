from typing import Dict, Any, Tuple


def validate_scan_payload(data: Dict[str, Any]) -> Tuple[str, int, int, str, str]:
    target = data.get("target")
    if not target:
        raise ValueError("Field 'target' is required")
    max_results = data.get("max_results", 4)
    if not isinstance(max_results, int) or max_results < 1 or max_results > 100:
        raise ValueError("max_results must be integer between 1 and 100")
    search_type = data.get("suggestion_by", 1)
    ai_key = data.get("ai_key")
    github_token = data.get("github_token")
    return target, max_results, search_type, ai_key, github_token


def map_suggestions(suggestions):
    return [
        {
            "title": s.get("title"),
            "detail": s.get("detail"),
            "priority": s.get("priority", "medium"),
            "source": s.get("source", "rule")
        }
        for s in suggestions
    ]
