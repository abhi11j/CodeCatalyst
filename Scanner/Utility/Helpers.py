"""
Utility helpers for the GitHub repository scanner project.
This module provides helper functions for common tasks like parsing GitHub repository
URLs and handling authentication tokens. These utilities are used across the scanner
project to maintain consistency and reduce code duplication.
Available functions:
    - parse_repo_url: Convert various GitHub URL formats to owner/repo format
    - get_github_token: Retrieve GitHub authentication token from environment
"""

from __future__ import annotations
import os
from typing import Optional
from urllib.parse import urlparse

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Helpers:
    """Parse a GitHub repository URL and return 'owner/repo'.
        Accepts URLs like:
        - https://github.com/owner/repo
        - git@github.com:owner/repo.git
        - owner/repo (returned unchanged)
    """
    def ParseRepoUrl(url: str) -> str:        
        if "://" in url or url.startswith("git@"):
            # handle git@ and https URLs
            if url.startswith("git@"):
                # git@github.com:owner/repo.git
                _, path = url.split(":", 1)
                if path.endswith(".git"):
                    path = path[:-4]
                return path.strip("/")
            parsed = urlparse(url)
            path = parsed.path.lstrip("/")
            if path.endswith(".git"):
                path = path[:-4]
            # remove possible trailing slash
            return path.strip("/")
        # assume already owner/repo
        return url

    """Return GitHub token from environment variables if present.
        The GitHub token can be obtained by following these steps:
        1. Go to GitHub.com and log in to your account
        2. Click on your profile picture → Settings
        3. Scroll down to "Developer settings" (bottom of left sidebar)
        4. Click on "Personal access tokens" → "Tokens (classic)"
        5. Click "Generate new token" → "Generate new token (classic)"
        6. Give your token a descriptive name
        7. Select scopes (at minimum, select 'public_repo' for public repositories)
        8. Click "Generate token"
        9. Copy the token immediately (it won't be shown again)
        10. Set the token in your environment:
            - Windows PowerShell: $env:GITHUB_TOKEN = 'your-token'
            - Windows CMD: set GITHUB_TOKEN=your-token
            - Linux/macOS: export GITHUB_TOKEN=your-token

        Looks for GITHUB_TOKEN or GH_TOKEN in environment variables.
        GITHUB_TOKEN is preferred over GH_TOKEN.
    """
    def GetGithubToken() -> Optional[str]:        
        return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    """Load environment variables from a simple `.env`-style file.
        Behavior:
            - Skip empty lines and comments starting with '#'
            - Support 'KEY=VALUE' pairs. Values may be quoted with single or double quotes
            - Do not override existing environment variables (useful for CI and local override)
    """
    def LoadEnvFile(filepath: str = ".env") -> None:        
        try:
            if not os.path.exists(filepath):
                logging.info(".inv file not found.")
                return
            
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # ignore comments and empty lines
                    if not line or line.startswith("#"):
                        continue
                    # allow lines like export KEY=VALUE
                    if line.startswith("export "):
                        line = line[len("export "):]
                    if "=" not in line:
                        continue
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip()
                    # strip surrounding quotes if present
                    if (val.startswith("\"") and val.endswith("\"")) or (val.startswith("'") and val.endswith("'")):
                        val = val[1:-1]
                    # don't override existing env variables
                    if key not in os.environ:
                        os.environ[key] = val
        except Exception:
            # Best-effort loader for convenience; failures shouldn't crash the CLI
            return
    