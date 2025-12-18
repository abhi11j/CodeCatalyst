import json
import requests

from Scanner.GitHub.GitHubClient import GitHubClient

class DummyResponse:
    def __init__(self, status_code, json_data=None):
        self.status_code = status_code
        self._json = json_data

    def json(self):
        if self._json is None:
            raise ValueError("No JSON")
        return self._json

class DummySession:
    def __init__(self, responses):
        # responses: dict of (method, url) -> DummyResponse
        self.responses = responses
        self.headers = {}

    def get(self, url, params=None):
        key = ("GET", url)
        return self.responses.get(key, DummyResponse(404))

    def head(self, url):
        key = ("HEAD", url)
        return self.responses.get(key, DummyResponse(404))


def test_get_repo_success():
    url = "https://api.github.com/repos/owner/repo"
    data = {"language": "Python", "stargazers_count": 10}
    sess = DummySession({("GET", url): DummyResponse(200, json_data=data)})
    client = GitHubClient(token=None, session=sess)
    repo = client.get_repo("owner/repo")
    assert repo["language"] == "Python"


def test_search_repositories():
    url = "https://api.github.com/search/repositories"
    payload = {"items": [{"full_name": "owner/repo1"}, {"full_name": "owner/repo2"}]}
    sess = DummySession({("GET", url): DummyResponse(200, json_data=payload)})
    client = GitHubClient(token=None, session=sess)
    results = client.search_repositories("language:Python", max_results=2)
    assert results == ["owner/repo1", "owner/repo2"]


def test_head_contents():
    url = "https://api.github.com/repos/owner/repo/contents/Dockerfile"
    sess = DummySession({("HEAD", url): DummyResponse(200)})
    client = GitHubClient(token=None, session=sess)
    assert client.head_contents("owner/repo", "Dockerfile") is True
