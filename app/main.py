from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from .api import create_router
from .database import SQLiteStore
from .resources import RESOURCES
from .ui import model_schema

app = FastAPI(
    title="Requirements Engineering Workbench",
    version="0.1.0",
    description="IREB-oriented Requirements Engineering API.",
)
store = SQLiteStore()
app.include_router(create_router(store, RESOURCES))


@app.get("/")
def root():
    return FileResponse(Path(__file__).parent / "static" / "index.html", media_type="text/html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/schema")
def get_model_schema():
    return model_schema()
