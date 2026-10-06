from dataclasses import dataclass
import sqlite3
from typing import Any, Callable

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .database import SQLiteStore


@dataclass(frozen=True)
class Resource:
    path: str
    table: str
    model: type[BaseModel]
    prefix: str


def create_router(store: SQLiteStore, resources: list[Resource]) -> APIRouter:
    router = APIRouter()
    for resource in resources:
        _register(router, store, resource)
    return router


def _register(router: APIRouter, store: SQLiteStore, resource: Resource) -> None:
    model = resource.model
    router.add_api_route(resource.path, _list(store, resource), methods=["GET"], response_model=list[model])
    router.add_api_route(resource.path, _create(store, resource), methods=["POST"], response_model=model, status_code=201)
    router.add_api_route(f"{resource.path}/{{item_id}}", _get(store, resource), methods=["GET"], response_model=model)
    router.add_api_route(f"{resource.path}/{{item_id}}", _update(store, resource), methods=["PUT"], response_model=model)


def _list(store: SQLiteStore, resource: Resource) -> Callable[[], list[Any]]:
    def endpoint() -> list[Any]:
        return store.list(resource.table, resource.model)
    return endpoint


def _create(store: SQLiteStore, resource: Resource) -> Callable[[resource.model], resource.model]:
    def endpoint(item: resource.model) -> resource.model:
        if not item.id:
            item.id = f"{resource.prefix}-{store.next_id(resource.table, resource.model):03d}"
        try:
            store.insert(resource.table, item)
        except sqlite3.IntegrityError:
            raise HTTPException(409, f"{resource.model.__name__} ID already exists")
        return item
    return endpoint


def _get(store: SQLiteStore, resource: Resource) -> Callable[[str], Any]:
    def endpoint(item_id: str) -> Any:
        item = store.get(resource.table, resource.model, item_id)
        if item is None:
            raise HTTPException(404, f"{resource.model.__name__} not found")
        return item
    return endpoint


def _update(store: SQLiteStore, resource: Resource) -> Callable[[resource.model, str], resource.model]:
    def endpoint(item_id: str, item: resource.model) -> resource.model:
        if item_id != item.id:
            raise HTTPException(400, f"{resource.model.__name__} ID cannot be changed")
        if not store.update(resource.table, item):
            raise HTTPException(404, f"{resource.model.__name__} not found")
        return item
    return endpoint
