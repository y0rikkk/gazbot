# Используем официальный Python образ
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы зависимостей
COPY pyproject.toml poetry.lock ./

# Устанавливаем Poetry (последняя версия)
RUN pip install --no-cache-dir poetry

# Конфигурируем Poetry (не создавать виртуальное окружение)
RUN poetry config virtualenvs.create false

# Устанавливаем зависимости (без dev-зависимостей)
RUN poetry install --no-interaction --no-ansi --no-root --only main

# Копируем весь проект
COPY . .

# Создаем директорию для логов
RUN mkdir -p logs

# Копируем entrypoint скрипт
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Открываем порт
EXPOSE 8000

# Устанавливаем entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]

# Запускаем приложение
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
