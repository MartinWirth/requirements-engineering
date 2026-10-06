from dataclasses import dataclass

import sqlite3
from typing import Any

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

    @router.get(resource.path, response_model=list[model])
    def list_items(r: Resource = resource) -> list[Any]:
        return store.list(r.table, r.model)

    @router.post(resource.path, response_model=model, status_code=201)
    def create_item(item: model, r: Resource = resource) -> model:
        if not item.id:
            item.id = f"{r.prefix}-{store.next_id(r.table, r.model):03d}"
        try:
            store.insert(r.table, item)
        except sqlite3.IntegrityError:
            raise HTTPException(409, f"{r.model.__name__} ID already exists")
        return item

    @router.get(f"{resource.path}/{{item_id}}", response_model=model)
    def get_item(item_id: str, r: Resource = resource) -> model:
        item = store.get(r.table, r.model, item_id)
        if item is None:
            raise HTTPException(404, f"{r.model.__name__} not found")
        return item

    @router.put(f"{resource.path}/{{item_id}}", response_model=model)
    def update_item(item_id: str, item: model, r: Resource = resource) -> model:
        if item_id != item.id:
            raise HTTPException(400, f"{r.model.__name__} ID cannot be changed")
        if not store.update(r.table, item):
            raise HTTPException(404, f"{r.model.__name__} not found")
        return item
