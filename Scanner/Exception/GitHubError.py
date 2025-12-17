
"""GitHub API error base class."""
from typing import Optional


class GitHubError(Exception):    
    
    def __init__(self, message: str, status_code: int):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

"""Base class used to indicate GitHub API level errors."""
class GitHubAPIError(Exception):        
    def __init__(self, message: str, status_code: int):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

"""Raised when GitHub API returns 403 rate limit exceeded."""
class GitHubRateLimitError(GitHubAPIError):
    def __init__(self, reset_time: Optional[int] = None, message: str = "Rate limit exceeded"):
        super().__init__(message)
        self.reset_time = reset_time

"""Raised when GitHub API returns 401 Unauthorized (invalid or missing token)."""
class GitHubUnauthorizedError(GitHubAPIError):        
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message)

"""Raised when GitHub API rate limit is exceeded.
        Attributes:
            reset_time: optional epoch seconds when rate limit resets
            message: message from API (if any)
"""
class GitHubRateLimitError(GitHubAPIError):
    def __init__(self, reset_time: Optional[int] = None, message: str = "Rate limit exceeded"):
        super().__init__(message)
        self.reset_time = reset_time

"""Raised when GitHub API returns 401 Unauthorized (invalid or missing token)."""
class GitHubUnauthorizedError(GitHubAPIError):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message)