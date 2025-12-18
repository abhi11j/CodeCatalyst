from __future__ import annotations
from typing import Any, Dict, Optional

from Scanner.GitHub.Interface.ISearchProvider import ISearchProvider
from Scanner.GitHub.AI.ai_client import AIClient
from Scanner.GitHub.AI.prompt_builder import build_prompt, build_complete_ai_prompt
from Scanner.GitHub.AI.response_parser import extract_suggestions_from_response

import logging
logger = logging.getLogger(__name__)


class AISuggestion(ISearchProvider):
    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None, model: Optional[str] = None):
        self.client = AIClient(api_key=api_key, endpoint=endpoint, model=model)

    def GenerateSuggestions(self, context: Dict[str, Any], target_url: Optional[str] = None, ai_only: bool = False) -> Dict[str, Any]:
        prompt = build_complete_ai_prompt(target_url) if ai_only else build_prompt(context)
        try:
            resp = self.client.generate(prompt)
            suggestions = extract_suggestions_from_response(resp["text"])
            for item in suggestions:
                item.update(source=resp.get("source", "ai"))
            return suggestions
        except Exception as e:
            logger.exception("AISuggestion failed: %s", e)
            raise
