"""URL utilities for repository parsing."""
from urllib.parse import urlparse


def parse_repo_url(url: str) -> str:
    if "://" in url or url.startswith("git@"):
        if url.startswith("git@"):
            _, path = url.split(":", 1)
            if path.endswith(".git"):
                path = path[:-4]
            return path.strip("/")
        parsed = urlparse(url)
        path = parsed.path.lstrip("/")
        if path.endswith(".git"):
            path = path[:-4]
        return path.strip("/")
    return url
