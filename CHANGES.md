## Refactor (2025-12-18)

Summary:
- Extracted `Scanner.GitHub.GitHubClient` to centralize GitHub HTTP calls and error handling (replaces ad-hoc requests usage in `ScanBusiness`).
- Added `Scanner.Business.RepoAnalyzer` to convert GitHub API responses into `RepoFeatures` and encapsulate repo checks.
- Split AI responsibilities into `Scanner.GitHub.AI.ai_client`, `prompt_builder`, and `response_parser` for clearer separation of concerns.
- Split `Scanner.Utility.Helpers` into focused modules: `env`, `url`, and `auth`. Kept a thin `Helpers` wrapper for backward compatibility.
- Added route validators in `Scanner.Routes.validators` and simplified `ScanRoute`.
- Fixed type imports in `RuleConfiguration.py`.
- Added basic unit tests for utils, AI response parsing, and route validators.

Next steps:
- Add unit tests for `GitHubClient` and `RepoAnalyzer` with HTTP mocking.
- Add integration tests for end-to-end scanning flow.
- Install and run tests (`pip install -r requirements.txt` then `pytest`).
- Consider further splitting and adding type annotations and docstrings where helpful.
