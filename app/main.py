from fastapi import FastAPI, HTTPException, Query
from pathlib import Path
import json
import re
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
        target.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(500, "Project specification could not be created") from exc
    return {"path": filename, "spec": spec}
