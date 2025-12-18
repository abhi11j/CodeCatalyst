"""
Lightweight GitHub API client to centralize HTTP interactions and error handling.
"""
from typing import Any, Dict, Optional, List
import os
import requests
from Scanner.Exception.GitHubError import GitHubError

class GitHubClient:
    def __init__(self, token: Optional[str] = None, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()
        token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if token:
            self.session.headers.update({"Authorization": f"token {token}"})
        # Accept header to read topics
        self.session.headers.update({"Accept": "application/vnd.github.mercy-preview+json"})
        self.base = os.environ.get("GITHUB_API_ROOT", "https://api.github.com")

    def _handle_response(self, response: requests.Response, repo: Optional[str] = None) -> Any:
        if response.status_code == 404:
            raise GitHubError(f"Repository not found: {repo}", 404)
        elif response.status_code == 401:
            raise GitHubError("Unauthorized: Invalid GitHub token", 401)
        elif response.status_code == 403:
            raise GitHubError("Rate limited: GitHub API quota exceeded", 429)
        elif response.status_code != 200:
            raise GitHubError(f"GitHub API error: {response.status_code}", response.status_code)
        try:
            return response.json()
        except ValueError:
            # Not all endpoints return JSON (HEAD), return raw response
            return response

    def get_repo(self, repo_full_name: str) -> Dict[str, Any]:
        url = f"{self.base}/repos/{repo_full_name}"
        response = self.session.get(url)
        return self._handle_response(response, repo_full_name)

    def search_repositories(self, query: str, max_results: int = 6) -> List[str]:
        url = f"{self.base}/search/repositories"
        params = {"q": query, "sort": "stars", "per_page": min(max_results, 100)}
        response = self.session.get(url, params=params)
        data = self._handle_response(response)
        return [item["full_name"] for item in data.get("items", [])][:max_results]

    def head_contents(self, repo_full_name: str, path: str) -> bool:
        url = f"{self.base}/repos/{repo_full_name}/contents/{path}"
        try:
            response = self.session.head(url)
            return response.status_code in (200, 302)
        except requests.exceptions.RequestException:
            return False
