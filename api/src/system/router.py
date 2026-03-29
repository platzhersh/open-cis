from fastapi import APIRouter

from src.system.schemas import SystemInfoResponse
from src.system.service import system_service

router = APIRouter()


@router.get("", response_model=SystemInfoResponse)
async def get_system_info() -> SystemInfoResponse:
    """Get system health, versions, registered templates, and data statistics."""
    return await system_service.get_system_info()
