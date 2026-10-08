import json

from app.github import _create_pull_request


def test_pull_request_payload(monkeypatch):
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({"html_url": "https://github.com/MartinWirth/requirements-engineering/pull/7", "number": 7}).encode()

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["headers"] = dict(req.headers)
        captured["payload"] = json.loads(req.data.decode())
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr("app.github.request.urlopen", fake_urlopen)
    result = _create_pull_request(
        "secret",
        "MartinWirth/requirements-engineering",
        "https://api.github.com",
        branch="ai/WI-001-implement",
        base="main",
        title="AI implementation: Implement requirement",
        body="summary",
    )

    assert result == {
        "url": "https://github.com/MartinWirth/requirements-engineering/pull/7",
        "number": 7,
    }
    assert captured["url"].endswith("/repos/MartinWirth/requirements-engineering/pulls")
    assert captured["payload"] == {
        "title": "AI implementation: Implement requirement",
        "body": "summary",
        "head": "ai/WI-001-implement",
        "base": "main",
        "draft": False,
    }
    assert captured["timeout"] == 30
    assert captured["headers"]["Authorization"] == "Bearer secret"
