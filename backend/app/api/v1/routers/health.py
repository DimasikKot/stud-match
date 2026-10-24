from fastapi import APIRouter
from pydantic import BaseModel

router: APIRouter = APIRouter()


class GetHealthResponse(BaseModel):
    detail: str
    success: bool


@router.get("/health", response_model=GetHealthResponse)
async def get_backend():
    return GetHealthResponse(detail="Backend контейнер исправно работает", success=True)
