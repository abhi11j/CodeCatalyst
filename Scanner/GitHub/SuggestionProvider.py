"""AI provider abstraction and implementations for suggestion generation.
This module provides a pluggable interface for using LLMs or mock providers to generate
repository improvement suggestions. The OpenAI-compatible provider uses the HTTP API
to call chat completions and returns a JSON-like structure.
"""

from __future__ import annotations
from Scanner.GitHub.Implementation.AISuggestion import AISuggestion
from Scanner.GitHub.Implementation.ManualSuggestion import ManualSuggestion
from Scanner.GitHub.Implementation.AutomatedSuggestion import AutomatedSuggestion
from Scanner.GitHub.Interface import ISearchProvider

import logging
logger = logging.getLogger(__name__)

class SuggestionProvider:
            
    """Initialize and return appropriate AI provider.    
        Args:
            openai_key: Optional OpenAI API key        
        Returns:
            AIProvider instance (OpenAI or Mock)
    """
    def InitializeProvider(search_type: int = 1, ai_key: str = None) -> ISearchProvider:    
        try:
            if search_type == 1:
                return AutomatedSuggestion()
            elif search_type == 2 or search_type == 3:
                return AISuggestion(api_key=ai_key)
            else:
                return ManualSuggestion()
        except Exception as e:
            logger.warning(f"Failed to initialize AI provider: {e}. Using Mock provider.")




