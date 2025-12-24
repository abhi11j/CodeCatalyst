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
        default_branch = data.get("default_branch", "main")

        features = RepoFeatures(
            name=repo_full_name,
            language=data.get("language", "Unknown"),
            stars=data.get("stargazers_count", 0),
            topics=data.get("topics", []),
            has_dockerfile=client.file_exists(repo_full_name, "Dockerfile", default_branch),
            has_ci=(
                client.file_exists(repo_full_name, ".github/workflows", default_branch)
                or client.file_exists(repo_full_name, ".travis.yml", default_branch)
            ),
            has_tests=(
                client.file_exists(repo_full_name, "tests", default_branch)
                or client.file_exists(repo_full_name, "test", default_branch)
            ),
            has_readme=client.file_exists(repo_full_name, "README.md", default_branch)
        )
        return features

