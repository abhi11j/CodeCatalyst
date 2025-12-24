"""
Simple parser functions for AI responses.
"""
import json
from typing import Any, List, Dict
import logging

logger = logging.getLogger(__name__)


def extract_suggestions_from_response(raw_text: str) -> List[Dict[str, Any]]:
    logger.info("Extracting suggestions JSON from AI response")
    outer = json.loads(raw_text)
    inner = outer["choices"][0]["message"]["content"]
    parsed = json.loads(inner)
    return parsed.get("suggestions", [])
