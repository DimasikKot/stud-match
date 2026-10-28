FROM python:3.12-slim

WORKDIR /app

# Показываем порт (необязательно)
EXPOSE 8060

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# hot-reload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8060", "--reload"]

# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8060"]