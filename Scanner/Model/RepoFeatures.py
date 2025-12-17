from dataclasses import dataclass
from typing import List

"""Repository features detected by analysis (API-focused)."""
@dataclass
class RepoFeatures:    
    name: str
    language: str
    stars: int
    topics: List[str]
    has_dockerfile: bool
    has_ci: bool
    has_tests: bool
    has_readme: bool