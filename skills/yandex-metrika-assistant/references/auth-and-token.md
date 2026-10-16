# Получение OAuth-токена для Яндекс.Метрики (Linux)

Этот скилл использует OAuth-токен Яндекса для доступа к API Метрики. Получение токена — одноразовая ручная операция.

## Шаг 1. Зарегистрируй OAuth-приложение

1. Открой https://oauth.yandex.ru/client/new
2. Название: любое (например, `claude-metrika-local`).
3. Платформа: **Веб-сервисы** → Redirect URI: `https://oauth.yandex.ru/verification_code`
4. Доступы (scopes) — отметь:
   - **Яндекс.Метрика** → `Получение статистики, чтение параметров счётчиков`
   - **Яндекс.Метрика** → `Изменение параметров своих счётчиков` (если планируешь изменять цели/счётчики через API; для read-only можно не отмечать)
   - **Яндекс.Метрика** → `Чтение логов` (если будешь использовать Logs API)
5. Сохрани приложение, скопируй **Client ID**.

## Шаг 2. Получи токен (Implicit Grant flow)

Открой в браузере:

```
https://oauth.yandex.ru/authorize?response_type=token&client_id=<CLIENT_ID>
```

Подтверди доступы. Тебя редиректнёт на страницу с verification code → URL вида:

```
https://oauth.yandex.ru/verification_code#access_token=y0_AgAAAA...&token_type=bearer&expires_in=31536000
```

Скопируй значение `access_token` (без `#access_token=`).

## Шаг 3. Сохрани токен в скилл

```bash
node ~/.claude/skills/yandex-metrika-assistant/scripts/setup.js
```

Вставь токен по запросу. Скрипт проверит токен через `management/v1/counters`, покажет твои счётчики и попросит выбрать default + назначить алиасы.

## Проверка вручную (curl)

```bash
TOKEN="y0_AgAAAA..."
curl -s -H "Authorization: OAuth $TOKEN" \
  https://api-metrika.yandex.net/management/v1/counters | jq .
```

Если ответ содержит `"counters": [...]` — токен валиден.

## Срок жизни токена

По умолчанию `expires_in = 31536000` секунд (1 год). После истечения — повтори шаг 2 и запусти `setup.js` снова.

## Если токен не работает

- HTTP 401 — токен невалиден или отозван. Получи новый.
- HTTP 403 на конкретный счётчик — у токена нет доступа к этому счётчику (ты не владелец/представитель).
- Quotas: см. [`quotas.md`](./quotas.md).
