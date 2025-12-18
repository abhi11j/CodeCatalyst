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

Patterns implemented:
- Added a thread-safe `Singleton` metaclass in `Scanner/Utils/singleton.py` and applied it to `Scanner/GitHub/GitHubClient.py` to centralize session reuse.
- Added `ProviderFactory` in `Scanner/GitHub/ProviderFactory.py` and updated `SuggestionProvider` to use the Factory pattern for provider creation.
- Added an `EventDispatcher` in `Scanner/Events/event_dispatcher.py` (Observer pattern) and wired `ScanBusiness` to emit `scan_started` and `scan_completed` events.

Other updates:
- Added `.github/TOPICS.md` with recommended repository topics and a `scripts/set_topics.py` utility to apply topics via the GitHub API.
- Added a GitHub Action workflow `.github/workflows/set-topics.yml` to apply topics automatically on push or via workflow dispatch.
