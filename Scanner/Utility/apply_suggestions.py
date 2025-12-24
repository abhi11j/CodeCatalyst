"""Utilities to apply improvement suggestions to the local repository.

This module provides functions used by the API endpoint to:
- create a branch from `main`
- apply suggestions (create files)
- commit & push changes
- open a PR via `gh` or the GitHub API
"""
from __future__ import annotations

import os
import subprocess
import time
import json
import tempfile
import shutil
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

# Lazy import of AI client to avoid hard dependency if not used
try:
    from Scanner.GitHub.AI.ai_client import AIClient
except Exception:
    AIClient = None

# Validation constants
MAX_CHANGE_COUNT = 50
MAX_CONTENT_SIZE = 200 * 1024  # 200 KB
ALLOWED_ACTIONS = {"add", "modify", "delete"}
# Protected top-level paths that should never be modified by AI
PROTECTED_PREFIXES = {".git", ".env", "secrets", "credentials"}

"""Ensure `path` is inside `root` after normalization."""
def _is_safe_subpath(root: str, path: str) -> bool:    
    root = os.path.realpath(root)
    target = os.path.realpath(os.path.join(root, path))
    return os.path.commonpath([root]) == os.path.commonpath([root, target])

"""Validate a single change entry from AI output. Raises ValueError on error."""
def _validate_change_entry(entry: dict, repo_dir: str) -> None:
    logger.info("Validating change entry: %s", entry)
    if not isinstance(entry, dict):
        logger.error("Invalid change entry (not an object): %s", entry)
        raise ValueError("Each change must be an object")
    path = entry.get("path")
    action = entry.get("action")
    if not path or not isinstance(path, str):
        logger.error("Missing or invalid 'path' in change entry: %s", entry)
        raise ValueError("Each change must include a string 'path'")
    if action not in ALLOWED_ACTIONS:
        logger.error("Invalid action '%s' in entry: %s", action, entry)
        raise ValueError(f"Invalid action '{action}'. Allowed: add, modify, delete")
    # Prevent path traversal
    if not _is_safe_subpath(repo_dir, path):
        logger.error("Path traversal detected for path '%s' (repo_dir=%s)", path, repo_dir)
        raise ValueError(f"Path '{path}' escapes repository root")
    # Prevent changes to protected prefixes
    for pfx in PROTECTED_PREFIXES:
        if path == pfx or path.startswith(pfx + "/"):
            logger.error("Attempt to modify protected path '%s'", path)
            raise ValueError(f"Modification of protected path '{path}' is not allowed")
    # Validate content size when present
    if action in ("add", "modify"):
        content = entry.get("content")
        if content is None or not isinstance(content, str):
            logger.error("'content' must be provided as string for add/modify: %s", entry)
            raise ValueError("'content' must be provided as a string for add/modify actions")
        if len(content.encode("utf-8")) > MAX_CONTENT_SIZE:
            logger.error("Content size for '%s' exceeds maximum (%d bytes)", path, MAX_CONTENT_SIZE)
            raise ValueError(f"Change content for '{path}' exceeds maximum allowed size of {MAX_CONTENT_SIZE} bytes")

def _run_git(cmd: List[str], cwd: Optional[str] = None) -> Optional[str]:
    cwd = cwd or os.getcwd()
    logger.debug("Running git command: %s cwd=%s", " ".join(cmd), cwd)
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)
        stdout = (result.stdout or "").strip()
        if stdout:
            logger.debug("git stdout: %s", stdout if len(stdout) < 2000 else stdout[:2000] + "...(truncated)")
        return stdout
    except subprocess.CalledProcessError as e:
        stdout = (e.stdout or "").strip()
        stderr = (e.stderr or "").strip()
        logger.error("Git command failed: %s", cmd)
        logger.error("Exit code: %s", getattr(e, "returncode", ""))
        if stdout:
            logger.error("git stdout: %s", stdout if len(stdout) < 2000 else stdout[:2000] + "...(truncated)")
        if stderr:
            logger.error("git stderr: %s", stderr if len(stderr) < 2000 else stderr[:2000] + "...(truncated)")
        raise


def _push_branch(repo_dir: str, branch_name: str, retries: int = 1, delay: float = 1.0) -> None:
    """Push branch to origin. Try '-u origin <branch>' first, fallback to 'origin HEAD:refs/heads/<branch>'
    and retry once if transient errors occur.
    """
    attempt = 0
    last_exc = None
    while attempt <= retries:
        attempt += 1
        try:
            logger.debug("Attempting git push (attempt %d) for branch %s", attempt, branch_name)
            _run_git(["git", "push", "-u", "origin", branch_name], cwd=repo_dir)
            logger.info("Successfully pushed branch %s to origin", branch_name)
            return
        except subprocess.CalledProcessError as e:
            last_exc = e
            logger.warning("Failed to push branch %s with -u origin: %s", branch_name, str(e))
            # try alternative push form
            try:
                logger.debug("Trying alternative push form HEAD:refs/heads/%s", branch_name)
                _run_git(["git", "push", "origin", f"HEAD:refs/heads/{branch_name}"], cwd=repo_dir)
                logger.info("Successfully pushed branch %s using HEAD:refs/heads/%s", branch_name, branch_name)
                return
            except subprocess.CalledProcessError as e2:
                last_exc = e2
                logger.warning("Alternative push also failed for branch %s: %s", branch_name, str(e2))

        if attempt <= retries:
            logger.info("Retrying push after %.1fs...", delay)
            time.sleep(delay)

    logger.error("Failed to push branch %s to origin after %d attempts.", branch_name, attempt)
    logger.error("Possible causes: authentication failure, insufficient permissions, branch protection, or upstream rejects.")
    raise last_exc

"""Apply a single non-AI suggestion using deterministic rules."""
def _apply_single_suggestion(suggestion: Dict[str, Any], repo_dir: Optional[str] = None) -> bool:   
    repo_dir = repo_dir or os.getcwd()
    title = suggestion.get("title", "").lower()
    detail = suggestion.get("detail", "")
    changed = False

    logger.info("Applying deterministic suggestion: %s", suggestion.get("title"))

    if "dockerfile" in title:
        path = os.path.join(repo_dir, "Dockerfile")
        if not os.path.exists(path):
            logger.info("Creating Dockerfile at %s", path)
            with open(path, "w", encoding="utf-8") as f:
                f.write("""# Simple Python app Dockerfile\nFROM python:3.11-slim\nWORKDIR /app\nCOPY requirements.txt ./\nRUN pip install -r requirements.txt\nCOPY . ./\nCMD ["python", "main.py"]\n""")
            changed = True
        else:
            logger.info("Dockerfile already exists at %s; skipping", path)

    elif "ci" in title or "workflow" in title:
        gh_dir = os.path.join(repo_dir, ".github", "workflows")
        os.makedirs(gh_dir, exist_ok=True)
        path = os.path.join(gh_dir, "ci.yml")
        if not os.path.exists(path):
            logger.info("Creating GitHub Actions workflow at %s", path)
            with open(path, "w", encoding="utf-8") as f:
                f.write("""name: CI\n\non: [push, pull_request]\n\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n      - uses: actions/setup-python@v4\n        with:\n          python-version: '3.11'\n      - name: Install deps\n        run: pip install -r requirements.txt\n      - name: Run tests\n        run: pytest -q\n""")
            changed = True
        else:
            logger.info("Workflow already exists at %s; skipping", path)

    elif "test" in title or "tests" in title:
        tests_dir = os.path.join(repo_dir, "tests")
        os.makedirs(tests_dir, exist_ok=True)
        path = os.path.join(tests_dir, "test_placeholder.py")
        if not os.path.exists(path):
            logger.info("Creating placeholder test at %s", path)
            with open(path, "w", encoding="utf-8") as f:
                f.write("""def test_placeholder():\n    assert True\n""")
            changed = True
        else:
            logger.info("Test placeholder already exists at %s; skipping", path)

    elif "readme" in title:
        path = os.path.join(repo_dir, "README.md")
        if not os.path.exists(path):
            logger.info("Creating README at %s", path)
            with open(path, "w", encoding="utf-8") as f:
                f.write("# Project\n\nThis project was improved by automated suggestions.\n")
            changed = True
        else:
            logger.info("README already exists at %s; skipping", path)

    else:
        docs_dir = os.path.join(repo_dir, "docs")
        os.makedirs(docs_dir, exist_ok=True)
        safe_name = title.replace(" ", "_").replace("/", "_")[:100]
        path = os.path.join(docs_dir, f"{safe_name}.md")
        if not os.path.exists(path):
            logger.info("Creating documentation file at %s", path)
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"# {suggestion.get('title')}\n\n{detail}\n")
            changed = True
        else:
            logger.info("Docs file already exists at %s; skipping", path)

    return changed

"""Use an AI agent to convert an instruction into filesystem changes.
    The AI is expected to return JSON structured as:
    {"changes": [{"path": "file/path.py", "action": "add|modify|delete", "content": "..."}, ...]}
    Returns True if any file was created/modified/deleted.
"""
def _apply_ai_instruction(suggestion: Dict[str, Any], repo_dir: Optional[str] = None, ai_key: Optional[str] = None, endpoint: Optional[str] = None, model: Optional[str] = None) -> bool:
    
    repo_dir = repo_dir or os.getcwd()
    instruction = suggestion.get("detail")
    if not instruction:
        logger.info("AI instruction missing 'detail' in suggestion: %s", suggestion)
        return False

    logger.info("Applying AI instruction: %s", suggestion.get("title"))

    if AIClient is None:
        logger.error("AI client not available when attempting to apply AI instruction")
        raise RuntimeError("AI client not available; set up AI client or provide ai_key in request")

    # Build a prompt that instructs the AI to return structured JSON
    prompt = (
        "You are a repository automation assistant.\n"
        "Given the instruction below, return a JSON object with a top-level 'changes' list.\n"
        "Each change must be an object with 'path', 'action' ('add'|'modify'|'delete'), and 'content' for add/modify.\n"
        "Do not include any extra text. Only output valid JSON.\n\n"
        f"Instruction:\n{instruction}\n\n"
        "Context: The repository root is available to modify files. Use relative paths.\n"
    )

    try:
        client = AIClient(api_key=ai_key, endpoint=endpoint, model=model)
        resp = client.generate(prompt)
        text = resp.get("text") if isinstance(resp, dict) else str(resp)
        logger.info("AI response text (truncated): %s", text[:2000])

        # Try to extract JSON from the response text
        parsed = None
        try:
            parsed = json.loads(text)
        except Exception:
            # Fallback: find first JSON object in text
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    parsed = json.loads(text[start:end+1])
                except Exception:
                    parsed = None

        if not parsed or "changes" not in parsed or not isinstance(parsed["changes"], list):
            logger.error("AI response did not contain a valid 'changes' list. Response: %s", text[:1000])
            raise ValueError("AI response did not contain a valid 'changes' list")

        changes = parsed["changes"]
        logger.info("AI produced %d changes", len(changes))
        if len(changes) > MAX_CHANGE_COUNT:
            logger.error("AI produced too many changes (%d); max is %d", len(changes), MAX_CHANGE_COUNT)
            raise ValueError(f"AI produced too many changes ({len(changes)}), max allowed is {MAX_CHANGE_COUNT})")

        changed_any = False
        # Validate all entries first
        for c in changes:
            _validate_change_entry(c, repo_dir)

        # Apply after successful validation
        for c in changes:
            rel_path = c.get("path")
            path = os.path.join(repo_dir, rel_path)
            action = c.get("action")
            if action in ("add", "modify"):
                logger.info("AI action %s -> %s", action, path)
                os.makedirs(os.path.dirname(path) or repo_dir, exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(c.get("content", ""))
                changed_any = True
            elif action == "delete":
                logger.info("AI action delete -> %s", path)
                if os.path.exists(path):
                    os.remove(path)
                    changed_any = True

        logger.info("AI instruction applied; changed_any=%s", changed_any)
        return changed_any
    except ValueError as ve:
        logger.warning("Validation error applying AI instruction: %s", ve)
        # Re-raise to allow upstream handling (HTTP 400)
        raise
    except Exception as e:
        logger.exception("AI instruction application failed: %s", e)
        # For safety, do not apply any partial changes on unexpected errors
        raise RuntimeError(f"AI instruction application failed: {e}")

"""Apply suggestions in a new branch and create a PR.   
    Returns a dict with keys: branch, changed_files (list of titles), pr_url (optional), message
"""
def apply_suggestions_to_branch(suggestions: List[Dict[str, Any]], branch_name: Optional[str] = None, github_token: Optional[str] = None, ai_key: Optional[str] = None, repo_dir: Optional[str] = None, target: Optional[str] = None, base_branch: str = "main") -> Dict[str, Any]:
    """Apply suggestions to a repository branch.

    If `target` (owner/repo or repo URL) is provided, this function will:
      - clone the target repo into a temporary directory
      - checkout `base_branch` from the remote
      - create `branch_name` from `base_branch`
      - apply changes and push the branch back to GitHub

    Returns the same dict as before, but includes `repo_dir` (path used) to help callers/tests inspect the workspace.
    """

    logger.info("Starting apply_suggestions_to_branch: suggestions=%d, branch=%s, target=%s", len(suggestions), branch_name, target)

    tmp_dir = None
    owner_repo = None

    # If a remote target is provided, clone it into a temporary directory
    if target:
        tmp_dir = tempfile.mkdtemp(prefix="apply_suggestions_")
        logger.info("Cloning target repository %s into %s", target, tmp_dir)
        # normalize owner/repo or accept full URL
        target_repo = target
        if target_repo.startswith("https://") or target_repo.startswith("git@"):
            repo_url = target_repo.rstrip(".git")
            if repo_url.endswith("/"):
                repo_url = repo_url[:-1]
            repo_url = repo_url if repo_url.endswith(".git") else repo_url + ".git"
            owner_repo = repo_url.split("github.com/")[-1].rstrip(".git")
            repo_clone_url = repo_url
        else:
            owner_repo = target_repo
            repo_clone_url = f"https://github.com/{owner_repo}.git"

        if github_token:
            # Do not log token directly
            repo_clone_url_auth = f"https://{github_token}@github.com/{owner_repo}.git"
            logger.info("Using token-auth clone URL for owner_repo=%s", owner_repo)
        else:
            repo_clone_url_auth = repo_clone_url

        try:
            # Clone only the target base branch for efficiency
            logger.info("Cloning repo %s branch %s", repo_clone_url_auth, base_branch)
            _run_git(["git", "clone", "--branch", base_branch, "--single-branch", "--depth", "1", repo_clone_url_auth, tmp_dir])
        except Exception:
            logger.exception("Failed to clone repository %s", target)
            # Cleanup on failure
            try:
                shutil.rmtree(tmp_dir)
            except Exception:
                pass
            raise
        repo_dir = tmp_dir

    repo_dir = repo_dir or os.getcwd()

    # Make a safe branch name
    if not branch_name:
        branch_name = f"auto/apply-suggestions-{int(time.time())}"
    logger.info("Using branch name: %s", branch_name)

    # Fetch base branch and create branch from it
    try:
        _run_git(["git", "fetch", "origin", base_branch], cwd=repo_dir)
    except Exception:
        # Proceed even if fetch fails (local-only repo)
        logger.info("Git fetch failed or not applicable for repo_dir=%s; continuing", repo_dir)
        pass

    _run_git(["git", "checkout", "-B", branch_name, base_branch], cwd=repo_dir)

    changed = []
    for s in suggestions:
        logger.info("Processing suggestion: %s", s.get("title"))
        try:
            # If suggestion contains an AI instruction, use AI to generate file changes
            if s.get("source") == "AI Cafe":
                try:
                    if _apply_ai_instruction(s, repo_dir=repo_dir, ai_key=ai_key):
                        logger.info("AI applied changes for suggestion: %s", s.get("title"))
                        changed.append(s.get("title"))
                except ValueError as ve:
                    # Validation error from AI output: stop and return details
                    logger.warning("Validation error from AI for suggestion %s: %s", s.get("title"), ve)
                    return {"branch": branch_name, "changed_files": changed, "message": "validation_error", "error": str(ve)}
                continue

            if _apply_single_suggestion(s, repo_dir=repo_dir):
                logger.info("Applied deterministic suggestion: %s", s.get("title"))
                changed.append(s.get("title"))
        except Exception as e:
            # Continue on individual failures but log them
            logger.exception("Failed to apply suggestion '%s': %s", s.get("title"), e)
            continue

    if not changed:
        logger.info("No changes were needed after processing suggestions")
        return {"branch": branch_name, "changed_files": [], "message": "No changes needed"}

    logger.info("Staging %d changed files and committing", len(changed))
    _run_git(["git", "add", "-A"], cwd=repo_dir)
    commit_msg = "Apply automated suggestions: " + ", ".join(changed)
    _run_git(["git", "commit", "-m", commit_msg], cwd=repo_dir)

    # Push branch (attempt to set token-auth remote if target + token provided)
    try:
        if target and github_token:
            # Ensure remote uses token auth so push can succeed for private repos
            auth_url = f"https://{github_token}@github.com/{owner_repo}.git"
            logger.info("Setting token-auth remote for owner_repo=%s", owner_repo)
            try:
                _run_git(["git", "remote", "set-url", "origin", auth_url], cwd=repo_dir)
            except Exception:
                logger.exception("Failed to set remote URL with token; continuing")
                # Not fatal
                pass
        _push_branch(repo_dir, branch_name)
    except Exception:
        logger.exception("Failed to push branch %s to origin; branch may be local", branch_name)
        # Non-fatal; branch may be local or push failed
        pass

    pr_url = None
    # Try gh CLI (use base_branch for PR base)
    try:
        logger.info("Attempting to create a PR via gh CLI")
        subprocess.check_call(["gh", "pr", "create", "--title", "Apply automated code improvements", "--body", commit_msg, "--base", base_branch, "--head", branch_name], cwd=repo_dir)
        # If gh succeeded, it usually prints the url, but we can't capture it easily here
        if owner_repo:
            pr_url = f"https://github.com/{owner_repo}/pull/new/{branch_name}"
        else:
            pr_url = f"https://github.com/<owner>/<repo>/pull/new/{branch_name}"
        logger.info("PR creation via gh CLI attempted; guess URL: %s", pr_url)
    except Exception:
        logger.warning("gh CLI failed or unavailable; falling back to GitHub API if token present")
        # Try GitHub API with token
        token = github_token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if token:
            try:
                import requests
                # Determine owner/repo from git remote if not known
                if not owner_repo:
                    try:
                        remote = subprocess.check_output(["git", "remote", "get-url", "origin"], cwd=repo_dir, text=True).strip()
                    except Exception:
                        remote = None
                    owner_repo = None
                    if remote:
                        if remote.startswith("https://"):
                            owner_repo = remote.rstrip(".git").split("github.com/")[-1]
                        elif remote.startswith("git@"):
                            owner_repo = remote.split(":", 1)[-1].rstrip(".git")
                if owner_repo:
                    api_url = f"https://api.github.com/repos/{owner_repo}/pulls"
                    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
                    payload = {"title": "Apply automated code improvements", "body": commit_msg, "head": branch_name, "base": base_branch}
                    logger.info("Attempting to create PR via GitHub API at %s", api_url)
                    resp = requests.post(api_url, json=payload, headers=headers)
                    if resp.status_code in (200, 201):
                        pr = resp.json()
                        pr_url = pr.get("html_url")
                        logger.info("PR created via API: %s", pr_url)
            except Exception:
                logger.exception("Failed to create PR via GitHub API")
                pass

    result = {"branch": branch_name, "changed_files": changed, "pr_url": pr_url, "message": "Applied suggestions", "repo_dir": repo_dir}
    logger.info("apply_suggestions_to_branch completed: branch=%s changed=%d pr_url=%s", branch_name, len(changed), pr_url)
    return result
