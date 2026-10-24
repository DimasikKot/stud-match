from fastapi import APIRouter

from app.api.v1.routers import health


api_router: APIRouter = APIRouter()


# В пути лучше всегда делать множественное число, тк так легче писать фронтэнд
api_router.include_router(health.router, prefix="/healths", tags=["Healths"])
