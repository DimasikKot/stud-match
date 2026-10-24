from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import api_router

app: FastAPI = FastAPI(root_path="/backend")


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
