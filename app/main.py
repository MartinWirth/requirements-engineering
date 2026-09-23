from pathlib import Path

import sqlite3

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from .database import SQLiteStore
from .models import Actor, Requirement, TraceLink, UseCase
from .ui import model_schema


app = FastAPI(
    title="Requirements Engineering Workbench",
    version="0.1.0",
    description="IREB-oriented Requirements Engineering API.",
)

store = SQLiteStore()


@app.get("/")
def root():
    return FileResponse(
        Path(__file__).parent / "static" / "index.html",
        media_type="text/html",
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/schema")
def get_model_schema():
    return model_schema()


@app.get("/requirements", response_model=list[Requirement])
def list_requirements():
    return store.list("requirements", Requirement)


@app.post("/requirements", response_model=Requirement, status_code=201)
def create_requirement(item: Requirement):
    if not item.id:
        item.id = f"REQ-{store.next_id('requirements', Requirement):03d}"
    try:
        store.insert("requirements", item)
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Requirement ID already exists")
    return item


@app.put("/requirements/{requirement_id}", response_model=Requirement)
def update_requirement(requirement_id: str, item: Requirement):
    if requirement_id != item.id:
        raise HTTPException(400, "Requirement ID cannot be changed")
    if not store.update("requirements", item):
        raise HTTPException(404, "Requirement not found")
    return item


@app.get("/requirements/{requirement_id}", response_model=Requirement)
def get_requirement(requirement_id: str):
    item = store.get("requirements", Requirement, requirement_id)
    if item is None:
        raise HTTPException(404, "Requirement not found")
    return item


@app.get("/use-cases", response_model=list[UseCase])
def list_use_cases():
    return store.list("use_cases", UseCase)


@app.post("/use-cases", response_model=UseCase, status_code=201)
def create_use_case(item: UseCase):
    if not item.id:
        item.id = f"UC-{store.next_id('use_cases', UseCase):03d}"
    try:
        store.insert("use_cases", item)
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Use-case ID already exists")
    return item


@app.put("/use-cases/{use_case_id}", response_model=UseCase)
def update_use_case(use_case_id: str, item: UseCase):
    if use_case_id != item.id:
        raise HTTPException(400, "Use-case ID cannot be changed")
    if not store.update("use_cases", item):
        raise HTTPException(404, "Use case not found")
    return item


@app.get("/use-cases/{use_case_id}", response_model=UseCase)
def get_use_case(use_case_id: str):
    item = store.get("use_cases", UseCase, use_case_id)
    if item is None:
        raise HTTPException(404, "Use case not found")
    return item


@app.get("/actors", response_model=list[Actor])
def list_actors():
    return store.list("actors", Actor)


@app.post("/actors", response_model=Actor, status_code=201)
def create_actor(item: Actor):
    if not item.id:
        item.id = f"ACT-{store.next_id('actors', Actor):03d}"
    try:
        store.insert("actors", item)
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Actor ID already exists")
    return item


@app.put("/actors/{actor_id}", response_model=Actor)
def update_actor(actor_id: str, item: Actor):
    if actor_id != item.id:
        raise HTTPException(400, "Actor ID cannot be changed")
    if not store.update("actors", item):
        raise HTTPException(404, "Actor not found")
    return item


@app.get("/traceability", response_model=list[TraceLink])
def list_traceability():
    return store.list("trace_links", TraceLink)


@app.post("/traceability", response_model=TraceLink, status_code=201)
def create_trace_link(item: TraceLink):
    if not item.id:
        item.id = f"TRACE-{store.next_id('trace_links', TraceLink):03d}"
    try:
        store.insert("trace_links", item)
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Trace link ID already exists")
    return item


@app.put("/traceability/{trace_link_id}", response_model=TraceLink)
def update_trace_link(trace_link_id: str, item: TraceLink):
    if trace_link_id != item.id:
        raise HTTPException(400, "Trace link ID cannot be changed")
    if not store.update("trace_links", item):
        raise HTTPException(404, "Trace link not found")
    return item
