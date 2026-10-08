from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from urllib import error, request


class GitHubIntegrationError(RuntimeError):
    pass


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise GitHubIntegrationError(f"Git command failed: {' '.join(args)}: {detail}")
    return result.stdout.strip()


def _config() -> tuple[str, str, str, str]:
    token = os.getenv("GITHUB_TOKEN", "").strip()
    repository = os.getenv("GITHUB_REPOSITORY", "").strip()
    base = os.getenv("GITHUB_BASE_BRANCH", "main").strip() or "main"
    api_url = os.getenv("GITHUB_API_URL", "https://api.github.com").rstrip("/")
    if not token:
        raise GitHubIntegrationError("GITHUB_TOKEN is not configured")
    if not repository or "/" not in repository:
        raise GitHubIntegrationError("GITHUB_REPOSITORY must be configured as owner/repository")
    return token, repository, base, api_url


def _create_pull_request(
    token: str,
    repository: str,
    api_url: str,
    *,
    branch: str,
    base: str,
    title: str,
    body: str,
) -> dict[str, object]:
    payload = json.dumps(
        {"title": title, "body": body, "head": branch, "base": base, "draft": False}
    ).encode("utf-8")
    req = request.Request(
        f"{api_url}/repos/{repository}/pulls",
        data=payload,
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace").strip()
        raise GitHubIntegrationError(
            f"GitHub pull request creation failed ({exc.code}): {detail}"
        ) from exc
    except (error.URLError, TimeoutError) as exc:
        raise GitHubIntegrationError(f"GitHub API request failed: {exc}") from exc
    return {"url": result.get("html_url", ""), "number": result.get("number")}


def publish_branch(
    root: Path,
    branch: str,
    title: str,
    body: str,
) -> dict[str, object]:
    token, repository, base, api_url = _config()
    if not branch or branch in {"main", base} or "/" not in branch:
        raise GitHubIntegrationError("Invalid AI branch for publication")

    remote = _git(root, "remote", "get-url", "origin")
    if not remote:
        raise GitHubIntegrationError("Git remote 'origin' is not configured")

    _git(root, "push", "--set-upstream", "origin", branch)
    return _create_pull_request(
        token,
        repository,
        api_url,
        branch=branch,
        base=base,
        title=title,
        body=body,
    )
