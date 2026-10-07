from fastapi import FastAPI, HTTPException, Query
from pathlib import Path
import json

from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

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
    if root not in spec.parents or spec.name.endswith("spec.json") is False or not spec.is_file():
        raise HTTPException(404, "Specification not found")
    try:
        return json.loads(spec.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(500, "Specification could not be loaded") from exc
