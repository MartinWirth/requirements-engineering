from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
import subprocess
import re
from pathlib import Path
from typing import Any


class AIExecutionError(RuntimeError):
    pass


def _config() -> tuple[str, str, str]:
    url=os.getenv("AI_API_URL","").strip()
    key=os.getenv("AI_API_KEY","").strip()
    model=os.getenv("AI_MODEL","").strip()
    if not url or not key or not model:
        raise AIExecutionError("AI API is not configured; set AI_API_URL, AI_API_KEY and AI_MODEL.")
    return url,key,model


def _project_files(root: Path, limit: int = 60000) -> str:
    allowed={".py",".js",".css",".html",".json",".md",".txt"}
    ignored={".git",".venv","venv","__pycache__","data","node_modules"}
    chunks=[]
    total=0
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in ignored or part==".git" for part in path.parts) or path.suffix.lower() not in allowed:
            continue
        try:
            content=path.read_text(encoding="utf-8")
        except (OSError,UnicodeDecodeError):
            continue
        block=f"FILE: {path.relative_to(root)}\n{content}\n"
        if total+len(block)>limit: continue
        chunks.append(block);total+=len(block)
    return "\n".join(chunks)


def execute_work_item(work_item: dict[str, Any], requirements: list[dict[str, Any]], root: Path) -> dict[str, Any]:
    url,key,model=_config()
    context=_project_files(root)
    prompt={
        "task": work_item,
        "requirements": requirements,
        "repository_files": context,
        "rules":[
            "Implement the work item in the repository.",
            "Return JSON only with keys summary, files, test_commands.",
            "files is a list of objects with path and content; include only files that must be created or changed.",
            "Do not modify .git, virtual environments, dependency caches, secrets, or files outside the repository.",
            "Preserve existing architecture and make the smallest coherent change.",
            "Add or update tests when appropriate.",
            "test_commands is a list of argument arrays, for example [\"pytest\",\"tests/test_workflow.py\"].",
            "Do not return markdown fences."
        ]
    }
    body=json.dumps({
        "model":model,
        "messages":[
            {"role":"system","content":"You are an autonomous software development agent working inside a Requirements Engineering Workbench repository."},
            {"role":"user","content":json.dumps(prompt)}
        ],
        "temperature":0
    }).encode()
    request=urllib.request.Request(url,data=body,headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},method="POST")
    try:
        with urllib.request.urlopen(request,timeout=120) as response:
            payload=json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError,TimeoutError,json.JSONDecodeError) as exc:
        raise AIExecutionError(f"AI API request failed: {exc}") from exc
    try:
        content=payload["choices"][0]["message"]["content"]
    except (KeyError,IndexError,TypeError) as exc:
        raise AIExecutionError("AI API response did not contain choices[0].message.content") from exc
    if isinstance(content,list):
        content="".join(part.get("text","") for part in content if isinstance(part,dict))
    try:
        result=json.loads(content)
    except json.JSONDecodeError as exc:
        raise AIExecutionError("AI response was not valid JSON") from exc
    if not isinstance(result,dict) or not isinstance(result.get("files"),list):
        raise AIExecutionError("AI response must contain a files list")
    return result



def commit_changes(root: Path, changed: list[str], work_item_id: str, title: str) -> dict[str, str]:
    def git(*args: str) -> str:
        result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=30, check=False)
        if result.returncode:
            raise AIExecutionError(result.stderr.strip() or f"git {' '.join(args)} failed")
        return result.stdout.strip()

    if git("status", "--porcelain"):
        raise AIExecutionError("Git working tree is not clean; AI execution will not overwrite existing local changes.")
    branch = f"ai/{work_item_id}-{re.sub(r'[^A-Za-z0-9_-]+', '-', title).strip('-')[:50]}"
    existing = subprocess.run(["git", "rev-parse", "--verify", branch], cwd=root, capture_output=True, text=True, check=False)
    if existing.returncode == 0:
        branch += "-2"
    git("switch", "-c", branch)
    git("add", "--", *changed)
    staged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=root, capture_output=True, text=True, check=False)
    if staged.returncode == 0:
        raise AIExecutionError("AI execution produced no Git changes.")
    git("commit", "-m", f"AI implement {work_item_id}: {title}")
    return {"branch": branch, "commit": git("rev-parse", "HEAD")}


def apply_changes(root: Path, result: dict[str, Any]) -> list[str]:
    changed=[]
    for item in result["files"]:
        if not isinstance(item,dict) or not isinstance(item.get("path"),str) or not isinstance(item.get("content"),str):
            raise AIExecutionError("AI returned an invalid file change")
        target=(root/item["path"]).resolve()
        if root not in target.parents or any(part==".git" for part in target.parts):
            raise AIExecutionError(f"AI attempted to write outside the repository: {item['path']}")
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(item["content"],encoding="utf-8")
        changed.append(str(target.relative_to(root)))
    return changed
