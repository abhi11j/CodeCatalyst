#!/usr/bin/env python3
"""Set GitHub repository topics using the REST API.

Reads topics from `.github/TOPICS.md` (lines that start with '- ') or accepts topics
from the command line. Requires GITHUB_TOKEN (with repo scope) and GITHUB_REPOSITORY
(or pass owner/repo as the first argument).
"""
import os
import sys
import json

try:
    import requests
except Exception:
    print("The 'requests' package is required. Install with: pip install requests")
    sys.exit(1)


def read_topics_from_file(path=".github/TOPICS.md"):
    if not os.path.exists(path):
        return []
    topics = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("- "):
                topics.append(line[2:].strip())
    return topics


def main():
    repo = os.environ.get("GITHUB_REPOSITORY") or (sys.argv[1] if len(sys.argv) > 1 else None)
    token = os.environ.get("GITHUB_TOKEN")
    if not repo:
        print("Repository not specified. Set GITHUB_REPOSITORY or pass owner/repo as first argument.")
        sys.exit(1)
    if not token:
        print("GITHUB_TOKEN not found in environment. Please set it (needs repo scope).")
        sys.exit(1)

    # topics: from args or file
    topics = sys.argv[2:] if len(sys.argv) > 2 else []
    if not topics:
        topics = read_topics_from_file()

    if not topics:
        print("No topics found. Either pass topics as args or create .github/TOPICS.md with a bullet list.")
        sys.exit(1)

    url = f"https://api.github.com/repos/{repo}/topics"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"token {token}",
        "Content-Type": "application/json"
    }
    payload = {"names": topics}

    resp = requests.put(url, headers=headers, json=payload)
    if resp.status_code in (200, 201):
        print(f"Successfully set topics for {repo}: {topics}")
        sys.exit(0)
    else:
        print(f"Failed to set topics: {resp.status_code} {resp.text}")
        sys.exit(2)


if __name__ == "__main__":
    main()
