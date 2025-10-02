# Dockerfile
FROM python:3.11-slim

# Установим утилиты (для сборки зависимостей и запуска проверки)
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential gcc netcat \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем зависимости и ставим
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Копируем проект
COPY . /app

# Копируем и делаем исполняемым скрипт ожидания БД
COPY wait_for_db.sh /app/wait_for_db.sh
RUN chmod +x /app/wait_for_db.sh

# Создадим непользовательского пользователя для безопасности
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

ENV PYTHONUNBUFFERED=1

CMD ["/app/wait_for_db.sh", "python", "main.py"]