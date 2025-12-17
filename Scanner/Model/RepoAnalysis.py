from dataclasses import dataclass
from typing import List, Optional, Dict

"""Extended repository analysis with additional metadata."""
@dataclass
class RepoAnalysis:    
    full_name: str
    description: Optional[str]
    language: Optional[str]
    topics: List[str]
    has_dockerfile: bool
    has_ci: bool
    has_tests: bool
    has_readme: bool
    stars: int
    forks: int
    license: Optional[str]
    languages: Dict[str, int]