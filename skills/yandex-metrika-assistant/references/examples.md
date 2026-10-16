# Примеры запросов к API (ручные и для отладки)

Перед вызовами нужны **OAuth-токен** и **id счётчика**. Токен не вставляйте в публичные репозитории и чаты. Получение токена: см. [`auth-and-token.md`](./auth-and-token.md).

Удобно задать переменные окружения в shell:

```bash
export YANDEX_METRIKA_OAUTH_TOKEN="<ваш_токен>"
export CID="99223440"   # подставьте свой counter id
```

Заголовок для всех запросов к `api-metrika.yandex.net`:

```http
Authorization: OAuth <access_token>
```

---

## 1. Список доступных счётчиков

```bash
curl -s -G "https://api-metrika.yandex.net/management/v1/counters" \
  --data-urlencode "per_page=50" \
  -H "Authorization: OAuth $YANDEX_METRIKA_OAUTH_TOKEN" \
  | jq '.counters[] | {id, name, site}'
```

Поиск по подстроке (название или домен):

```bash
curl -s -G "https://api-metrika.yandex.net/management/v1/counters" \
  --data-urlencode "search_string=blog" \
  --data-urlencode "per_page=20" \
  -H "Authorization: OAuth $YANDEX_METRIKA_OAUTH_TOKEN" | jq .
```

---

## 2. Визиты по дням за последние 30 дней

```bash
curl -s -G "https://api-metrika.yandex.net/stat/v1/data" \
  --data-urlencode "ids=$CID" \
  --data-urlencode "dimensions=ym:s:date" \
  --data-urlencode "metrics=ym:s:visits" \
  --data-urlencode "date1=30daysAgo" \
  --data-urlencode "date2=yesterday" \
  --data-urlencode "sort=ym:s:date" \
  -H "Authorization: OAuth $YANDEX_METRIKA_OAUTH_TOKEN" | jq .
```

---

## 3. Топ страниц по просмотрам (хиты)

В одном запросе используется только префикс **`ym:pv:`**.

```bash
curl -s -G "https://api-metrika.yandex.net/stat/v1/data" \
  --data-urlencode "ids=$CID" \
  --data-urlencode "dimensions=ym:pv:URL" \
  --data-urlencode "metrics=ym:pv:pageviews" \
  --data-urlencode "sort=-ym:pv:pageviews" \
  --data-urlencode "limit=15" \
  --data-urlencode "date1=30daysAgo" \
  --data-urlencode "date2=yesterday" \
  -H "Authorization: OAuth $YANDEX_METRIKA_OAUTH_TOKEN" | jq .
```

---

## 4. Отчёт по шаблону (preset) — «источники, сводка»

```bash
curl -s -G "https://api-metrika.yandex.net/stat/v1/data" \
  --data-urlencode "ids=$CID" \
  --data-urlencode "preset=sources_summary" \
  --data-urlencode "date1=7daysAgo" \
  --data-urlencode "date2=yesterday" \
  -H "Authorization: OAuth $YANDEX_METRIKA_OAUTH_TOKEN" | jq .
```

Другие пресеты: [шаблоны в доке Метрики](https://yandex.ru/dev/metrika/ru/stat/presets).

---

## 5. Выгрузка в CSV

Добавьте суффикс **`.csv`** к пути метода:

```
https://api-metrika.yandex.net/stat/v1/data.csv?ids=...&metrics=...&dimensions=...
```

```bash
curl -s -G "https://api-metrika.yandex.net/stat/v1/data.csv" \
  --data-urlencode "ids=$CID" \
  --data-urlencode "dimensions=ym:s:date" \
  --data-urlencode "metrics=ym:s:visits,ym:s:pageviews" \
  --data-urlencode "date1=7daysAgo" \
  --data-urlencode "date2=yesterday" \
  -H "Authorization: OAuth $YANDEX_METRIKA_OAUTH_TOKEN" \
  > visits.csv
```

---

## 6. Получение OAuth-токена

См. [`auth-and-token.md`](./auth-and-token.md) — инструкция по Implicit Grant flow для Linux.

---

## Ограничения

- Квоты: см. [`quotas.md`](./quotas.md).
- Имена метрик и группировок — только из [официального справочника](https://yandex.ru/dev/metrika/ru/stat/).
