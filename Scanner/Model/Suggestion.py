from dataclasses import dataclass

"""Improvement suggestion for a repository."""
@dataclass
class Suggestion:    
    title: str
    details: str
    priority: str = "medium"
    source: str = "rules"