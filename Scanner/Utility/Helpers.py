"""
Backward-compatible helpers wrapper. Prefer importing the focused functions from
`Scanner.Utility.env`, `Scanner.Utility.url`, and `Scanner.Utility.auth` instead.
"""
from Scanner.Utility.url import parse_repo_url
from Scanner.Utility.env import load_env_file
from Scanner.Utility.auth import get_github_token

class Helpers:
    @staticmethod
    def ParseRepoUrl(url: str) -> str:
        return parse_repo_url(url)

    @staticmethod
    def GetGithubToken():
        return get_github_token()

    @staticmethod
    def LoadEnvFile(filepath: str = ".env"):
        return load_env_file(filepath)

    