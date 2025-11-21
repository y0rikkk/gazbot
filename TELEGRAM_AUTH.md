# Telegram Web App Authentication

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

### 4. Использование в роутерах

**До (старый способ):**

```python
@router.get("/me")
def get_user(telegram_id: int, db: Session = Depends(get_db)):
    user = user_crud.get_user_by_telegram_id(db, telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

**После (с CurrentUser):**

```python
from app.core.auth import CurrentUser

@router.get("/me")
def get_user(current_user: CurrentUser):
    return current_user  # Пользователь уже готов!
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

### Получить приветствие

```bash
curl -X GET "http://localhost:8000/api/users/greeting" \
  -H "X-Telegram-Init-Data: query_id=...&user=...&hash=..."
```

## Преимущества

✅ **Безопасность** - криптографическая проверка данных  
✅ **Автоматизация** - пользователь создается автоматически  
✅ **Удобство** - не нужно передавать telegram_id везде  
✅ **Чистый код** - `CurrentUser` dependency используется везде одинаково  
✅ **Актуальность** - всегда свежая информация из Telegram

## Важно

1. **Telegram Bot Token должен быть в `.env`**

   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```

2. **CORS настроен только для `https://web.telegram.org`**

   - В production нужно добавить свой домен

3. **initData действителен 24 часа**

   - После этого пользователь должен перезапустить Web App

4. **Все endpoints теперь требуют `X-Telegram-Init-Data` заголовок**
   - Кроме `/` и `/health`
