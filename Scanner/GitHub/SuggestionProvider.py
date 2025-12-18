"""AI provider abstraction and implementations for suggestion generation.
This module provides a pluggable interface for using LLMs or mock providers to generate
repository improvement suggestions.
"""

from __future__ import annotations
from typing import Optional
from Scanner.GitHub.Implementation.AISuggestion import AISuggestion
from Scanner.GitHub.Implementation.ManualSuggestion import ManualSuggestion
from Scanner.GitHub.Implementation.AutomatedSuggestion import AutomatedSuggestion
from Scanner.GitHub.Interface import ISearchProvider
from Scanner.GitHub.ProviderFactory import ProviderFactory

import logging
logger = logging.getLogger(__name__)

# Register built-in providers
ProviderFactory.register("automated", lambda: AutomatedSuggestion())
ProviderFactory.register("ai", lambda api_key=None: AISuggestion(api_key=api_key))
ProviderFactory.register("manual", lambda: ManualSuggestion())

class SuggestionProvider:
    """Facade that uses `ProviderFactory` to create suggestion providers by type.
    This makes it easy to register new providers and test them.
    """

    @staticmethod
    def InitializeProvider(search_type: int = 1, ai_key: Optional[str] = None) -> ISearchProvider:
        mapping = {1: "automated", 2: "ai", 3: "ai", 4: "manual"}
        key = mapping.get(search_type, "automated")
        try:
            if key == "ai":
                return ProviderFactory.create(key, ai_key)
            return ProviderFactory.create(key)
        except KeyError as e:
            logger.warning("Provider not found: %s, falling back to automated", e)
            return ProviderFactory.create("automated")




