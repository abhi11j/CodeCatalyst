"""Authentication helpers"""
import os
from typing import Optional


def get_github_token() -> Optional[str]:
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
