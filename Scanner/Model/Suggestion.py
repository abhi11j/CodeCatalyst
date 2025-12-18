from dataclasses import dataclass

"""Improvement suggestion for a repository."""
@dataclass
class Suggestion:    
    title: str
    detail: str
    priority: str = "medium"
    source: str = "rules"