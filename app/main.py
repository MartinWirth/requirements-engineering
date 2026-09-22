from fastapi import FastAPI, HTTPException
from .models import Actor, Requirement, TraceLink, UseCase

app = FastAPI(
    title="Requirements Engineering Workbench",
    version="0.1.0",
    description="IREB-oriented Requirements Engineering API.",
)

requirements: dict[str, Requirement] = {}
use_cases: dict[str, UseCase] = {}
actors: dict[str, Actor] = {}
trace_links: list[TraceLink] = []


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "Requirements Engineering Workbench",
        "version": app.version,
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/requirements", response_model=list[Requirement])
def list_requirements():
    return list(requirements.values())


@app.post("/requirements", response_model=Requirement, status_code=201)
def create_requirement(item: Requirement):
    if item.id in requirements:
        raise HTTPException(409, "Requirement ID already exists")
    requirements[item.id] = item
    return item


@app.get("/requirements/{requirement_id}", response_model=Requirement)
def get_requirement(requirement_id: str):
    if requirement_id not in requirements:
        raise HTTPException(404, "Requirement not found")
    return requirements[requirement_id]


@app.get("/use-cases", response_model=list[UseCase])
def list_use_cases():
    return list(use_cases.values())


@app.post("/use-cases", response_model=UseCase, status_code=201)
def create_use_case(item: UseCase):
    if item.id in use_cases:
        raise HTTPException(409, "Use-case ID already exists")
    use_cases[item.id] = item
    return item


@app.get("/use-cases/{use_case_id}", response_model=UseCase)
def get_use_case(use_case_id: str):
    if use_case_id not in use_cases:
        raise HTTPException(404, "Use case not found")
    return use_cases[use_case_id]


@app.get("/actors", response_model=list[Actor])
def list_actors():
    return list(actors.values())


@app.post("/actors", response_model=Actor, status_code=201)
def create_actor(item: Actor):
    if item.id in actors:
        raise HTTPException(409, "Actor ID already exists")
    actors[item.id] = item
    return item


@app.get("/traceability", response_model=list[TraceLink])
def list_traceability():
    return trace_links


@app.post("/traceability", response_model=TraceLink, status_code=201)
def create_trace_link(item: TraceLink):
    trace_links.append(item)
    return item
