"""
Module to transform GitHub API responses into `RepoFeatures` and provide analysis helpers.
"""
from typing import Any
from Scanner.Model.RepoFeatures import RepoFeatures
from Scanner.Exception.GitHubError import GitHubError
from Scanner.GitHub.GitHubClient import GitHubClient

class RepoAnalyzer:
    @staticmethod
    def analyze_repo(repo_full_name: str, client: GitHubClient) -> RepoFeatures:
        data = client.get_repo(repo_full_name)
        # data is expected to be the parsed JSON from the GitHub API
        features = RepoFeatures(
            name=repo_full_name,
            language=data.get("language", "Unknown"),
            stars=data.get("stargazers_count", 0),
            topics=data.get("topics", []),
            has_dockerfile=client.head_contents(repo_full_name, "Dockerfile"),
            has_ci=(client.head_contents(repo_full_name, ".github/workflows") or client.head_contents(repo_full_name, ".travis.yml")),
            has_tests=(client.head_contents(repo_full_name, "tests") or client.head_contents(repo_full_name, "test")),
            has_readme=client.head_contents(repo_full_name, "README.md")
        )
        return features
