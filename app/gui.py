from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse

GUI_INDEX = Path(__file__).parent / "static" / "index.html"


def create_gui_router() -> APIRouter:
    router = APIRouter(tags=["GUI"])

    @router.get("/gui", include_in_schema=False)
    @router.get("/gui/", include_in_schema=False)
    def gui():
        return FileResponse(GUI_INDEX, media_type="text/html")

    return router
