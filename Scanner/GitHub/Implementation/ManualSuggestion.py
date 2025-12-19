from __future__ import annotations
from typing import Any, Dict, Optional
from Scanner.GitHub.Interface.ISearchProvider import ISearchProvider
from Scanner.Utility.RuleConfiguration import DEFAULT_COMPARISON_RULES

import logging
logger = logging.getLogger(__name__)

"""Deterministic mock provider used for tests and offline behavior.
    This produces suggestions based on simple heuristics so we don't depend on a remote API.
"""
class ManualSuggestion(ISearchProvider):
    def GenerateSuggestions(self, context: Dict[str, Any], target_url: Optional[str] = None, ai_only: bool = False) -> Dict[str, Any]:
        target = context.get("target", {})
        others = context.get("others", [])
        r = DEFAULT_COMPARISON_RULES
        suggestions = []
        if not target.has_dockerfile and any(o.has_dockerfile for o in others):
            suggestions.append({"title": "Add " + r["dockerfile"]["field"][4:], "detail": r["dockerfile"]["add_msg"], "priority": "high" if r["dockerfile"]["threshold"] > 0.8 else "medium" if r["dockerfile"]["threshold"] > 0.4 else "low"})
        if not target.has_ci and any(o.has_ci for o in others):
            suggestions.append({"title": "Add " + r["ci"]["field"][4:], "detail": r["ci"]["add_msg"], "priority": "high" if r["ci"]["threshold"] > 0.8 else "medium" if r["ci"]["threshold"] > 0.4 else "low"})
        if not target.has_tests and any(o.has_tests for o in others):
            suggestions.append({"title": "Add " + r["tests"]["field"][4:], "detail": r["tests"]["add_msg"], "priority": "high" if r["tests"]["threshold"] > 0.8 else "medium" if r["tests"]["threshold"] > 0.4 else "low"})
        if not target.has_readme and any(o.has_readme for o in others):
            suggestions.append({"title": "Add " + r["readme"]["field"][4:], "detail": r["readme"]["add_msg"], "priority": "high" if r["readme"]["threshold"] > 0.8 else "medium" if r["readme"]["threshold"] > 0.4 else "low"})
        
        for item in suggestions:
            item.update(source="Manual")

        return suggestions