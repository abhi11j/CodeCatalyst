import json
import os
import subprocess
import types
from Scanner.Routes.ScanRoute import CreateApp


class DummyProc:
    def __init__(self):
        pass


def test_apply_suggestions_endpoint(monkeypatch, tmp_path):
    app = CreateApp()
    client = app.test_client()

    # Prepare payload
    # Test both deterministic and AI-driven suggestions
    payload = {
        "target": "owner/repo",
        "search_type": 3,
        "suggestions": [
            {"title": "Add CI", "detail": "Add CI workflow"},
            {"title": "Add README", "detail": "Add README.md"},
            {"title": "AI: Add file", "ai_instruction": "Add a file named ai_added.txt at the repo root with content 'hello ai'"}
        ],
        "branch": "auto/test-apply"
    }

    # Monkeypatch subprocess.check_call to not execute real git commands
    def fake_check_call(cmd, cwd=None):
        # Allow check_call for mkdir etc but noop
        return 0

    def fake_check_output(cmd, cwd=None, text=None):
        # Return a fake origin remote
        return "https://github.com/owner/repo.git"

    monkeypatch.setattr(subprocess, "check_call", fake_check_call)
    monkeypatch.setattr(subprocess, "check_output", fake_check_output)

    # Monkeypatch requests.post used for PR creation
    class DummyResp:
        def __init__(self):
            self.status_code = 201

        def json(self):
            return {"html_url": "https://github.com/owner/repo/pull/1"}

    import builtins
    import importlib
    reqs = importlib.import_module("requests")
    monkeypatch.setattr(reqs, "post", lambda *a, **k: DummyResp())

    # Monkeypatch AIClient to return a JSON describing a file to add
    import importlib
    apply_module = importlib.import_module("Scanner.Utility.apply_suggestions")

    class DummyAIClient:
        def __init__(self, api_key=None, endpoint=None, model=None):
            pass
        def generate(self, prompt):
            return {"text": '{"changes": [{"path": "ai_added.txt", "action": "add", "content": "hello ai"}] }'}

    monkeypatch.setattr(apply_module, "AIClient", DummyAIClient)

    res = client.post("/api/apply-suggestions", json={**payload, "ai_key": "dummy"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    result = data["result"]
    assert "branch" in result
    assert result["changed_files"]
    # ai_added.txt should be applied
    assert os.path.exists(os.path.join(os.getcwd(), "ai_added.txt"))
    assert result["pr_url"] in (None, "https://github.com/owner/repo/pull/1")

    # ---------- Negative tests: malformed AI output and path traversal ----------
    class BadAIClientMalformed:
        def __init__(self, api_key=None, endpoint=None, model=None):
            pass
        def generate(self, prompt):
            return {"text": 'not a json'}

    monkeypatch.setattr(apply_module, "AIClient", BadAIClientMalformed)
    res = client.post("/api/apply-suggestions", json={"target":"owner/repo","search_type":3,"suggestions":[{"title":"AI bad","ai_instruction":"do stuff"}], "ai_key":"dummy"})
    assert res.status_code == 400 or res.status_code == 200
    data = res.get_json()
    # When malformed, we expect a validation error message or failure
    assert data.get("result") is None or data.get("result", {}).get("message") == "validation_error"

    class BadAIClientTraversal:
        def __init__(self, api_key=None, endpoint=None, model=None):
            pass
        def generate(self, prompt):
            return {"text": '{"changes":[{"path":"../etc/passwd","action":"add","content":"root:x:0:0"}] }'}

    monkeypatch.setattr(apply_module, "AIClient", BadAIClientTraversal)
    res = client.post("/api/apply-suggestions", json={"target":"owner/repo","search_type":3,"suggestions":[{"title":"AI bad","ai_instruction":"do stuff"}], "ai_key":"dummy"})
    # Should return a validation error (400) or indicate validation failure in result
    assert res.status_code == 400 or (res.get_json().get("result") and res.get_json()["result"].get("message") == "validation_error")

    class BadAIClientAction:
        def __init__(self, api_key=None, endpoint=None, model=None):
            pass
        def generate(self, prompt):
            return {"text": '{"changes":[{"path":"safe.txt","action":"rename","content":"x"}] }'}

    monkeypatch.setattr(apply_module, "AIClient", BadAIClientAction)
    res = client.post("/api/apply-suggestions", json={"target":"owner/repo","search_type":3,"suggestions":[{"title":"AI bad","ai_instruction":"do stuff"}], "ai_key":"dummy"})
    assert res.status_code == 400 or (res.get_json().get("result") and res.get_json()["result"].get("message") == "validation_error")

    # Oversize content
    large_content = "x" * (210 * 1024)
    class BadAIClientLarge:
        def __init__(self, api_key=None, endpoint=None, model=None):
            pass
        def generate(self, prompt):
            return {"text": json.dumps({"changes":[{"path":"big.txt","action":"add","content": large_content}]})}

    monkeypatch.setattr(apply_module, "AIClient", BadAIClientLarge)
    res = client.post("/api/apply-suggestions", json={"target":"owner/repo","search_type":3,"suggestions":[{"title":"AI bad","ai_instruction":"do stuff"}], "ai_key":"dummy"})
    assert res.status_code == 400 or (res.get_json().get("result") and res.get_json()["result"].get("message") == "validation_error")


def test_ai_instruction_requires_key(client=None):
    # Ensure endpoint enforces ai_key when ai_instruction present
    app = CreateApp()
    client = app.test_client()
    payload = {"target":"owner/repo","search_type":3,"suggestions":[{"title":"AI missing key","ai_instruction":"create something"}]}
    res = client.post("/api/apply-suggestions", json=payload)
    assert res.status_code == 400
    data = res.get_json()
    assert data["error"] == "invalid_parameter"
    assert "ai_key" in data["message"]
