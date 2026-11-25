from app.api.v1.routers import (
    files,
    healths,
    projects,
    students,
    users,
    zips,
)
from fastapi import APIRouter

api_router: APIRouter = APIRouter()


# В пути лучше всегда делать множественное число, тк так легче писать фронтэнд
api_router.include_router(users.router)
api_router.include_router(files.router)
api_router.include_router(files.internal_router)
api_router.include_router(zips.router)
api_router.include_router(students.router)
api_router.include_router(projects.router)
api_router.include_router(healths.router)
