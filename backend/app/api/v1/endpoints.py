from fastapi import APIRouter

from app.api.v1.routers import user
from app.api.v1.routers import echo
from app.api.v1.routers import project

from app.api.v1.routers import file
from app.api.v1.routers import model
from app.api.v1.routers import train

api_router: APIRouter = APIRouter()


# В пути лучше всегда делать множественное число, тк так легче писать фронтэнд
api_router.include_router(echo.router, prefix="/echos", tags=["Echos"])
# api_router.include_router(user.router, prefix="/users", tags=["Users"])
# api_router.include_router(project.router, prefix="/projects", tags=["Projects"])


# api_router.include_router(
#     file.router, prefix="/projects/{project_id}/files", tags=["Files"]
# )
# api_router.include_router(
#     model.router, prefix="/projects/{project_id}/models", tags=["Models"]
# )
# api_router.include_router(train.router, prefix="/ml", tags=["ML Endpoints"])
