from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from app.api.v1.endpoints import api_router

app: FastAPI = FastAPI(root_path="/backend")


def _fix_binary_schema(node):
    """contentMediaType -> format: binary, чтобы Swagger UI рисовал file picker."""
    if isinstance(node, dict):
        if node.get("contentMediaType") == "application/octet-stream":
            del node["contentMediaType"]
            node["format"] = "binary"
        for value in node.values():
            _fix_binary_schema(value)
    elif isinstance(node, list):
        for item in node:
            _fix_binary_schema(item)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        routes=app.routes,
    )
    _fix_binary_schema(schema)
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi


# Разрешённые источники
origins: list[str] = [
    "https://localhost",  # Фронтенд на Vite
    "https://127.0.0.1",  # Альтернативный локальный хост
    "https://stud-match.mooo.com",
]

# Добавляем CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Кто может делать запросы
    allow_credentials=True,
    allow_methods=["*"],  # Разрешенные методы (GET, POST и т.д.)
    allow_headers=["*"],  # Разрешенные заголовки
)


# Подключение всех роутеров API
app.include_router(api_router, prefix="/api/v1")
