from fastapi import FastAPI, HTTPException, Query
from pathlib import Path
import json
import re

from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .api import create_router
from .database import SQLiteStore
from .gui import create_gui_router
from .resources import RESOURCES
from .ui import model_schema

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
