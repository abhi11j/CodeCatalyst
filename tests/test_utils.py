from Scanner.Utility.url import parse_repo_url


def test_parse_https_url():
    assert parse_repo_url("https://github.com/owner/repo") == "owner/repo"


def test_parse_git_ssh_url():
    assert parse_repo_url("git@github.com:owner/repo.git") == "owner/repo"


def test_pass_through_owner_repo():
    assert parse_repo_url("owner/repo") == "owner/repo"
