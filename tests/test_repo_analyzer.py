from Scanner.GitHub.GitHubClient import GitHubClient
from Scanner.Business.RepoAnalyzer import RepoAnalyzer

class DummyResponse:
    def __init__(self, status_code, json_data=None):
        self.status_code = status_code
        self._json = json_data

    def json(self):
        return self._json

class DummySession:
    def __init__(self, responses):
        self.responses = responses
        self.headers = {}

    def get(self, url):
        return self.responses.get(("GET", url), DummyResponse(404))

    def head(self, url):
        return self.responses.get(("HEAD", url), DummyResponse(404))


def test_analyze_repo_features():
    repo_url = "https://api.github.com/repos/owner/repo"
    repo_data = {"language": "Python", "stargazers_count": 5, "topics": ["a"]}
    sess = DummySession({
        ("GET", repo_url): DummyResponse(200, json_data=repo_data),
        ("HEAD", "https://api.github.com/repos/owner/repo/contents/Dockerfile"): DummyResponse(200),
        ("HEAD", "https://api.github.com/repos/owner/repo/contents/.github/workflows"): DummyResponse(404),
        ("HEAD", "https://api.github.com/repos/owner/repo/contents/tests"): DummyResponse(404),
        ("HEAD", "https://api.github.com/repos/owner/repo/contents/README.md"): DummyResponse(200),
    })
    client = GitHubClient(token=None, session=sess)
    features = RepoAnalyzer.analyze_repo("owner/repo", client)
    assert features.language == "Python"
    assert features.has_dockerfile is True
    assert features.has_readme is True
