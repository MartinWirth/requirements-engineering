from fastapi import FastAPI, HTTPException, Query
from pathlib import Path
import json
import re
import subprocess
from datetime import datetime, timezone


from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .api import create_router
from .database import SQLiteStore
from .gui import create_gui_router
from .resources import RESOURCES
from .ui import model_schema
from .models import Requirement, TestCase, TraceLink, WorkItem, WorkItemType
from .ai import AIExecutionError, apply_changes, commit_changes, execute_work_item
from .github import GitHubIntegrationError, publish_branch

app = FastAPI(title="Requirements Engineering Workbench", version="0.1.0",
              description="API-driven Requirements Engineering GUI server.")

store = SQLiteStore()
app.include_router(create_router(store, RESOURCES))
app.include_router(create_gui_router())
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/gui")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/schema")
def get_model_schema():
    return model_schema()


@app.post("/api/requirements/{requirement_id}/generate")
def generate_workflow(requirement_id: str):
    req = store.get("requirements", Requirement, requirement_id)
    if not req:
        raise HTTPException(404, "Requirement not found")
    n = store.next_id("work_items", WorkItem)
    task = WorkItem(id=f"WI-{n:03d}", title=f"Implement: {req.title}", description=req.statement,
                    type=WorkItemType.TASK, priority=req.priority, requirement_ids=[req.id],
                    acceptance_criteria=req.acceptance_criteria)
    store.insert("work_items", task)
    t = store.next_id("test_cases", TestCase)
    test = TestCase(id=f"TEST-{t:03d}", title=f"Verify: {req.title}", description=f"Verify requirement {req.id}.",
                    status="ready", requirement_ids=[req.id], work_item_ids=[task.id],
                    steps=["Execute the implemented behavior."],
                    expected_results=req.acceptance_criteria or [req.statement])
    store.insert("test_cases", test)
    l = store.next_id("trace_links", TraceLink)
    store.insert("trace_links", TraceLink(id=f"TRACE-{l:03d}", source_id=task.id, target_id=req.id, relation="satisfies"))
    store.insert("trace_links", TraceLink(id=f"TRACE-{l + 1:03d}", source_id=test.id, target_id=req.id, relation="verifies"))
    return {"work_item": task, "test_case": test}

@app.get("/api/projects")
def get_projects():
    root = Path(__file__).parent.parent
    return sorted(str(p.relative_to(root)) for p in root.rglob("*spec.json") if ".git" not in p.parts)


@app.get("/api/project-spec")
def get_project_spec(path: str = Query(...)):
    root = Path(__file__).parent.parent.resolve()
    spec = (root / path).resolve()
    if root not in spec.parents or not spec.name.endswith("spec.json") or not spec.is_file():
        raise HTTPException(404, "Specification not found")
    try:
        return json.loads(spec.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(500, "Specification could not be loaded") from exc


class TestExecution(BaseModel):
    status: str
    actual_result: str = ""


@app.post("/api/test-cases/{test_case_id}/execute")
def execute_test_case(test_case_id: str, execution: TestExecution):
    test = store.get("test_cases", TestCase, test_case_id)
    if not test:
        raise HTTPException(404, "Test case not found")
    if execution.status not in {"passed", "failed", "blocked"}:
        raise HTTPException(400, "Execution status must be passed, failed, or blocked")
    test.status = execution.status
    test.actual_result = execution.actual_result
    test.executed_at = datetime.now(timezone.utc).isoformat()
    store.update("test_cases", test)
    return test


@app.post("/api/test-cases/{test_case_id}/run")
def run_test_case(test_case_id: str):
    test = store.get("test_cases", TestCase, test_case_id)
    if not test:
        raise HTTPException(404, "Test case not found")
    if not test.execution_command:
        raise HTTPException(400, "No execution command configured")
    try:
        result = subprocess.run(test.execution_command, cwd=Path(__file__).parent.parent,
                                capture_output=True, text=True, timeout=60, check=False)
    except subprocess.TimeoutExpired:
        test.status, output = "blocked", "Test execution timed out after 60 seconds."
    except OSError as exc:
        test.status, output = "blocked", f"Test execution could not start: {exc}"
    else:
        test.status = "passed" if result.returncode == 0 else "failed"
        output = (result.stdout + ("
" + result.stderr if result.stderr else "")).strip()
        output = f"exit code: {result.returncode}
{output}".strip()
    test.actual_result = output
    test.executed_at = datetime.now(timezone.utc).isoformat()
    store.update("test_cases", test)
    return test


class ProjectSpecCreate(BaseModel):
    name: str
    title: str = ""


@app.post("/api/project-spec")
def create_project_spec(request: ProjectSpecCreate):
    root = Path(__file__).parent.parent.resolve()
    name = re.sub(r"[^A-Za-z0-9_-]+", "-", request.name.strip()).strip("-_")
    if not name:
        raise HTTPException(400, "Project name is required")
    filename = name if name.endswith("spec.json") else name + "-spec.json"
    target = (root / filename).resolve()
    if root not in target.parents:
        raise HTTPException(400, "Invalid project name")
    if target.exists():
        raise HTTPException(409, "Project specification already exists")
    template = root / "requirements-engineering-spec.json"
    try:
        spec = json.loads(template.read_text(encoding="utf-8"))
        spec["$id"] = filename
        spec["title"] = request.title.strip() or name.replace("-", " ").replace("_", " ").title()
        target.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "
", encoding="utf-8")
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(500, "Project specification could not be created") from exc
    return {"path": filename, "spec": spec}


@app.post("/api/work-items/{work_item_id}/ai-execute")
def ai_execute_work_item(work_item_id: str):
    work_item = store.get("work_items", WorkItem, work_item_id)
    if not work_item:
        raise HTTPException(404, "Work item not found")
    requirements = [store.get("requirements", Requirement, rid) for rid in work_item.requirement_ids]
    requirements = [r.model_dump() for r in requirements if r]
    root = Path(__file__).parent.parent.resolve()
    work_item.status = "in_progress"
    store.update("work_items", work_item)
    try:
        result = execute_work_item(work_item.model_dump(), requirements, root)
        changed = apply_changes(root, result)
        git_info = commit_changes(root, changed, work_item.id, work_item.title)
        commands = result.get("test_commands") or []
        output = []
        status = "done"
        for command in commands[:3]:
            if not isinstance(command,list) or not all(isinstance(x,str) for x in command):
                continue
            try:
                test = subprocess.run(command,cwd=root,capture_output=True,text=True,timeout=60,check=False)
                output.append(f"$ {' '.join(command)}
exit code: {test.returncode}
{test.stdout}{test.stderr}".strip())
                if test.returncode != 0:
                    status = "in_review"
            except (OSError,subprocess.TimeoutExpired) as exc:
                output.append(f"$ {' '.join(command)}
blocked: {exc}")
                status = "blocked"
        work_item.status = status
        work_item.ai_summary = result.get("summary","")
        work_item.ai_executed_at = datetime.now(timezone.utc).isoformat()
        work_item.ai_branch = git_info["branch"]
        work_item.ai_commit = git_info["commit"]
        store.update("work_items", work_item)
        return {"work_item": work_item, "changed_files": changed, "git": git_info, "test_output": "

".join(output)}
    except AIExecutionError as exc:
        work_item.status = "blocked"
        work_item.ai_summary = str(exc)
        work_item.ai_executed_at = datetime.now(timezone.utc).isoformat()
        store.update("work_items", work_item)
        raise HTTPException(502, str(exc)) from exc
    except Exception as exc:
        work_item.status = "blocked"
        work_item.ai_summary = str(exc)
        work_item.ai_executed_at = datetime.now(timezone.utc).isoformat()
        store.update("work_items", work_item)
        raise HTTPException(500, "AI development execution failed") from exc


@app.post("/api/work-items/{work_item_id}/publish")
def publish_work_item(work_item_id: str):
    work_item = store.get("work_items", WorkItem, work_item_id)
    if not work_item:
        raise HTTPException(404, "Work item not found")
    if not work_item.ai_branch or not work_item.ai_commit:
        raise HTTPException(400, "Work item has no AI branch and commit to publish")
    try:
        result = publish_branch(
            root=Path(__file__).parent.parent.resolve(),
            branch=work_item.ai_branch,
            title=f"AI implementation: {work_item.title}",
            body=(
                f"Automated AI implementation for Work Item {work_item.id}.\n\n"
                f"AI summary:\n{work_item.ai_summary or '(none)'}\n\n"
                f"Commit: {work_item.ai_commit}"
            ),
        )
        work_item.ai_pr_url = result["url"]
        work_item.ai_pushed_at = datetime.now(timezone.utc).isoformat()
        store.update("work_items", work_item)
        return {"work_item": work_item, "github": result}
    except GitHubIntegrationError as exc:
        raise HTTPException(502, str(exc)) from exc
