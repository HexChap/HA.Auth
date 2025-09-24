from fastapi import APIRouter

from app.schemas import APIInfo
from app.settings import settings

router = APIRouter(tags=["misc"])


@router.get("/api-info")
async def get_api_info():
    return APIInfo(
        api_version=str(settings.api.version),
        build_version=str(settings.api.build_version),
    )
