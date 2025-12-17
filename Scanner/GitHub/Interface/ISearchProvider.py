"""
Search provider abstraction and implementations for query handling.
This module defines the pluggable interface ISearchProvider, which allows different
search backends (e.g., external APIs, mock providers, or custom engines) to be
integrated seamlessly. Implementations of ISearchProvider are responsible for
executing search requests and returning structured results in a consistent format.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class ISearchProvider(ABC):
    """Abstract search provider interface."""

    @abstractmethod
    def GenerateSuggestions(self, context: Dict[str, Any], target_url: Optional[str] = None, ai_only: bool = False) -> Dict[str, Any]:
        """Generate suggestions based on the given context."""
        pass