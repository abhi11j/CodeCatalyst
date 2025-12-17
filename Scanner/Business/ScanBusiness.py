from dataclasses import asdict
import json
import os
import requests

from typing import Dict, List, Optional, Any
from Scanner.Exception.GitHubError import GitHubError
from Scanner.Model.RepoFeatures import RepoFeatures
from Scanner.Utility.Helpers import Helpers
from Scanner.GitHub.SuggestionProvider import SuggestionProvider

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class ScanBusiness:

    """Initialize GitHub Scanner with optional token."""
    def __init__(self, token: Optional[str] = None):
        
        self.session = requests.Session()
        token = token or Helpers.GetGithubToken()
        if token:
            self.session.headers.update({"Authorization": f"token {token}"})
        # Accept header to read topics (historical preview header still accepted)
        self.session.headers.update({"Accept": "application/vnd.github.mercy-preview+json"})

    
    """Scan a GitHub repository and provide improvement suggestions (API-focused).    
        Args:
            target: Repository name (owner/repo format)
            max_results: Number of similar repos to analyze (1-100)
            github_token: Optional GitHub token (overrides env)
            search_type: Whether to use AI for suggestions
            rules: Optional custom rules        
        Returns:
            Scan results with suggestions and statistics
    """
    def ScanRepository(self, target: str, max_results: int = 6, search_type: int = 1, ai_key: Optional[str] = None) -> Dict[str, Any]:
        if not target:
            raise ValueError("target is required")
        if not (1 <= max_results <= 100):
            raise ValueError("max_results must be between 1 and 100")
        
        repos_context: Dict[str, Any] = {}

        if search_type != 3:        
            my_github_project_features = self.GetRepoFeatures(target)
            query = f"language:{my_github_project_features.language} stars:>{my_github_project_features.stars // 2}"
            similar_github_repos = self.SearchRepos(query, max_results)

            similar_github_project_features = []
            for github_repos in similar_github_repos:
                try:
                    similar_github_project_features.append(self.GetRepoFeatures(github_repos))
                except GitHubError:
                    continue          
            
            repos_context["target"] = my_github_project_features
            repos_context["others"] = similar_github_project_features

        target_url = f"{os.environ.get("GITHUB_API_ROOT")}/repos/{target}"
        suggestions = SuggestionProvider.InitializeProvider(search_type, ai_key).GenerateSuggestions(repos_context, target_url, search_type == 3)
            
        logger.info("suggestion %e", suggestions)
        
        return {
            "target": target,
            "success": True,
            "suggestions": suggestions
        }
    
    """Analyze repository and extract features (simpler interface)."""
    def GetRepoFeatures(self, repo: str) -> RepoFeatures:        
        url = f"{os.environ.get("GITHUB_API_ROOT")}/repos/{repo}"
        response = requests.get(url, headers=self.session.headers)
        
        if response.status_code == 404:
            raise GitHubError(f"Repository not found: {repo}", 404)
        elif response.status_code == 401:
            raise GitHubError("Unauthorized: Invalid GitHub token", 401)
        elif response.status_code == 403:
            raise GitHubError("Rate limited: GitHub API quota exceeded", 429)
        elif response.status_code != 200:
            raise GitHubError(f"GitHub API error: {response.status_code}", response.status_code)
        
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            raise GitHubError(f"JSON parse error: {e}", 500)
        
        # Extract features
        features = RepoFeatures(
            name=repo,
            language=data.get("language", "Unknown"),
            stars=data.get("stargazers_count", 0),
            topics=data.get("topics", []),
            has_dockerfile=self.CheckFileExists(repo, "Dockerfile"),
            has_ci=self.CheckFileExists(repo, ".github/workflows") or self.CheckFileExists(repo, ".travis.yml"),
            has_tests=self.CheckFileExists(repo, "tests") or self.CheckFileExists(repo, "test"),
            has_readme=self.CheckFileExists(repo, "README.md")
        )        
        return features
    
    """Search for similar repositories (simpler interface)."""
    def SearchRepos(self, query: str, max_results: int = 6) -> List[str]:        
        url = f"{os.environ.get("GITHUB_API_ROOT")}/search/repositories"
        params = {"q": query, "sort": "stars", "per_page": min(max_results, 100)}
        
        response = requests.get(url, headers=self.session.headers, params=params)
        
        if response.status_code == 401:
            raise GitHubError("Unauthorized: Invalid GitHub token", 401)
        elif response.status_code == 403:
            raise GitHubError("Rate limited: GitHub API quota exceeded", 429)
        elif response.status_code != 200:
            raise GitHubError(f"GitHub API error: {response.status_code}", response.status_code)
        
        try:
            data = response.json()
            return [item["full_name"] for item in data.get("items", [])][:max_results]
        except json.JSONDecodeError as e:
            raise GitHubError(f"JSON parse error: {e}", 500)

    """Check if file/directory exists in repository."""
    def CheckFileExists(self, repo: str, path: str) -> bool:        
        url = f"{os.environ.get("GITHUB_API_ROOT")}/repos/{repo}/contents/{path}"
        response = requests.head(url, headers=self.session.headers)
        return response.status_code in (200, 302)