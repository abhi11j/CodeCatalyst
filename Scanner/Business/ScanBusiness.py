from dataclasses import asdict
import json
import os

from typing import Dict, List, Optional, Any
from Scanner.Exception.GitHubError import GitHubError
from Scanner.Model.RepoFeatures import RepoFeatures
from Scanner.Utility.auth import get_github_token
from Scanner.GitHub.SuggestionProvider import SuggestionProvider
from Scanner.GitHub.GitHubClient import GitHubClient
from Scanner.Business.RepoAnalyzer import RepoAnalyzer

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

from Scanner.Events.event_dispatcher import EventDispatcher

class ScanBusiness:

    """High-level orchestrator that uses smaller, focused components to scan repos.
    Emits events via `EventDispatcher` (scan_started, scan_completed).
    """
    def __init__(self, token: Optional[str] = None, dispatcher: EventDispatcher = None):
        token = token or get_github_token()
        self.client = GitHubClient(token=token)
        # Use provided dispatcher or create a local one (callers can subscribe)
        self.dispatcher = dispatcher or EventDispatcher()

    def ScanRepository(self, target: str, max_results: int = 6, search_type: int = 1, ai_key: Optional[str] = None) -> Dict[str, Any]:
        if not target:
            raise ValueError("target is required")
        if not (1 <= max_results <= 100):
            raise ValueError("max_results must be between 1 and 100")

        repos_context: Dict[str, Any] = {}

        # Emit scan_started event
        try:
            self.dispatcher.dispatch("scan_started", target=target)
        except Exception:
            pass

        if search_type != 3:
            # Analyze the target repository
            my_github_project_features = RepoAnalyzer.analyze_repo(target, self.client)
            # Build search query from features
            query = f"language:{my_github_project_features.language} stars:>{my_github_project_features.stars // 2}"
            similar_github_repos = self.client.search_repositories(query, max_results)

            similar_github_project_features = []
            for github_repos in similar_github_repos:
                try:
                    similar_github_project_features.append(RepoAnalyzer.analyze_repo(github_repos, self.client))
                except GitHubError:
                    continue

            repos_context["target"] = my_github_project_features
            repos_context["others"] = similar_github_project_features

        target_url = f"{os.environ.get('GITHUB_API_ROOT')}/repos/{target}"
        provider = SuggestionProvider.InitializeProvider(search_type, ai_key)
        suggestions = provider.GenerateSuggestions(repos_context, target_url, search_type == 3)

        # Emit scan_completed event with result
        try:
            self.dispatcher.dispatch("scan_completed", target=target, suggestions=suggestions)
        except Exception:
            pass

        logger.info("suggestions: %s", suggestions)

        return {
            "target": target,
            "success": True,
            "suggestions": suggestions
        }
