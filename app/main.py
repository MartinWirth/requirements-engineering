from fastapi import FastAPI
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
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/gui")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/schema")
def get_model_schema():
    return model_schema()
