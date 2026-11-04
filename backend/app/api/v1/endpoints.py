from fastapi import APIRouter

from app.api.v1.routers import healths, users, projects, students

api_router: APIRouter = APIRouter()


# В пути лучше всегда делать множественное число, тк так легче писать фронтэнд
api_router.include_router(healths.router)
api_router.include_router(users.router)
api_router.include_router(projects.router)
api_router.include_router(students.router)
