from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings

router: APIRouter = APIRouter()


class GetEchoResponse(BaseModel):
    detail: str
    success: bool


@router.get("/health", response_model=GetEchoResponse)
async def get_backend():
    return GetEchoResponse(detail="Backend контейнер исправно работает", success=True)
