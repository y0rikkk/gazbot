# Database Management Commands

## Alembic Migrations

### Создать новую миграцию (автогенерация)

```bash
poetry run alembic revision --autogenerate -m "описание изменений"
```

### Применить миграции

```bash
poetry run alembic upgrade head
```

### Откатить последнюю миграцию

```bash
poetry run alembic downgrade -1
```

### Посмотреть текущую версию БД

```bash
poetry run alembic current
```

### Посмотреть историю миграций

```bash
poetry run alembic history
```

## Запуск приложения

### Development режим (с auto-reload)

```bash
poetry run uvicorn app.main:app --reload
```

### Production режим

```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Проверка БД

### Подключиться к PostgreSQL (psql)

```bash
psql -U postgres -d gazbot
```

### Посмотреть все таблицы

```sql
\dt
```

### Посмотреть структуру таблицы

```sql
\d users
\d events
\d registrations
```
