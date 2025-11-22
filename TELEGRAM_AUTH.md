# Telegram Web App Authentication by чатгпт

## Как это работает

### 1. Frontend (Telegram Web App)

```javascript
// Получаем initData из Telegram
const initData = window.Telegram.WebApp.initData;

// Все запросы к API отправляем с заголовком
fetch("http://your-api.com/api/users/me", {
  headers: {
    "X-Telegram-Init-Data": initData,
    "Content-Type": "application/json",
  },
})
  .then((response) => response.json())
  .then((user) => {
    console.log("Пользователь:", user);
    // Автоматически получили и создали пользователя!
  });
```

### 2. Что происходит в initData

При открытии Web App, Telegram автоматически передает:

```json
{
  "query_id": "AAHdF6IQAAAAAN0XohDhrOrc",
  "user": {
    "id": 123456789,
    "first_name": "John",
    "last_name": "Doe",
    "username": "johndoe",
    "language_code": "en"
  },
  "auth_date": 1702123456,
  "hash": "abc123..."
}
```

### 3. Backend проверяет подлинность

```python
# app/core/auth.py

# 1. Парсит initData
# 2. Проверяет HMAC-SHA256 hash с использованием bot token
# 3. Проверяет что данные не старше 24 часов
# 4. Создает пользователя в БД если его нет
# 5. Возвращает User объект
```

## Примеры запросов

### Получить профиль

```bash
curl -X GET "http://localhost:8000/api/users/me" \
  -H "X-Telegram-Init-Data: query_id=...&user=...&hash=..."
```

### Обновить профиль

```bash
curl -X PUT "http://localhost:8000/api/users/me" \
  -H "X-Telegram-Init-Data: query_id=...&user=...&hash=..." \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Ivan",
    "phone": "+79001234567",
    "isu": 312345
  }'
```

### Зарегистрироваться на мероприятие

```bash
curl -X POST "http://localhost:8000/api/events/1/register" \
  -H "X-Telegram-Init-Data: query_id=...&user=...&hash=..." \
  -H "Content-Type: application/json" \
  -d '{
    "user_data": {
      "first_name": "Ivan",
      "last_name": "Ivanov",
      "phone": "+79001234567",
      "isu": 312345
    }
  }'
```
