---
name: yandex-metrika-assistant
description: Use when the user asks about Yandex.Metrika data — traffic, sources, search queries, period comparison, or any metrika.yandex.ru analytics task. Triggers - "метрика", "трафик на <site>", "посещаемость", "источники трафика", "поисковые запросы", "сравни <period>", "Y.Metrika", "Yandex Metrika API", "ym:s:".
---

# Яндекс.Метрика — нативный Claude Code скилл

Скилл даёт мне 4 готовых сценария + 2 helper-скрипта на Node.js поверх API Метрики (`api-metrika.yandex.net`). Токен и алиасы счётчиков лежат в `~/.config/yandex-metrika/config.json`.

## Quick triage

1. **Конфига нет** (`~/.config/yandex-metrika/config.json` отсутствует, `YANDEX_METRIKA_OAUTH_TOKEN` не установлен) → попроси пользователя запустить `node ~/.claude/skills/yandex-metrika-assistant/scripts/setup.js`. Если токена ещё нет — отправь его в `references/auth-and-token.md`.
2. **Конфиг есть** → сразу к скрипту по таблице ниже.
3. **Вопрос про API напрямую** (не «покажи трафик», а «как фильтровать по UTM в Logs API») → читай `references/`, отвечай на основе доков.

## Recipe table — что запускать

Все скрипты в `~/.claude/skills/yandex-metrika-assistant/scripts/`. Запуск через **Bash tool**.

| Запрос пользователя                       | Команда                                                                  |
|-------------------------------------------|--------------------------------------------------------------------------|
| «трафик за неделю/месяц»                  | `node traffic-by-day.js --from 7daysAgo --format json`                   |
| «откуда люди приходят»                    | `node traffic-sources.js --from 30daysAgo --format json`                 |
| «откуда люди приходят с UTM-разбивкой»    | `node traffic-sources.js --from 30daysAgo --utm --format json`           |
| «что ищут (Я.Поиск/Google)»               | `node search-queries.js --engine yandex --format json`                   |
| «сравни с предыдущим периодом»            | `node compare-periods.js --period 7d --format json`                      |
| «какие у меня счётчики»                   | `node list-counters.js --format json`                                    |

Дополнительные флаги: `--counter <alias|id>` (без флага — default из config), `--limit N`, `--from/--to <date>` (формат Метрики: `7daysAgo`, `2026-04-01`, `yesterday`).

## Run rules (для меня)

1. Запускай через Bash tool с **`--format json`** — мне так удобнее парсить и интерпретировать.
2. Пользователю в ответе показывай **числа из JSON** + краткий вывод (что выросло/упало, что в топе). При желании пользователя «покажи как есть» — повтори с `--format table`.
3. Если пользователь не указал счётчик — используй default. **Одной строкой** упомяни в ответе: «использую счётчик `<alias>` (default из config)».
4. Если пользователь спрашивает про несколько сайтов сразу («трафик на всех») — циклом по `counters` из config + сводная таблица.
5. **Никогда не передавай токен как аргумент CLI.** Скрипты читают его сами из env/config.

## Security

- Токен **никогда** не должен попадать в stdout/stderr/коммит. Если в выводе видишь строку `y0_AgAA…` — это утечка, останавливайся, чисти лог, ищи причину.
- `~/.config/yandex-metrika/config.json` — `chmod 600`, один на пользователя.
- Конфиг **вне** директории скилла, чтобы переустановка скилла не трогала секреты.

## References

- `references/auth-and-token.md` — как получить OAuth-токен на Linux (Implicit Grant).
- `references/api-base.md` — базовый URL, формат ответов.
- `references/stat-api.md` — `/stat/v1/data`: метрики (`ym:s:*`, `ym:pv:*`), измерения, фильтры, сортировка.
- `references/logs-api.md` — Logs API (выгрузка сырых логов; пока не покрыт скриптами).
- `references/management-api.md` — счётчики, цели, сегменты.
- `references/quotas.md` — лимиты, что делать при HTTP 429.
- `references/intents-matrix.md` — матрица «задача пользователя → endpoint API».
- `references/examples.md` — копипастные `curl`-примеры.

## Adding a new scenario

1. Создай `scripts/<name>.js`, копируй структуру `traffic-by-day.js`.
2. Переиспользуй `lib/config.js` (токен + counter), `lib/api.js` (HTTP), `lib/format.js` (вывод), `lib/args.js` (флаги).
3. Запусти `node --check scripts/<name>.js` для синтаксической проверки.
4. Добавь строку в Recipe table выше.
5. Тестовый запуск с `--format json` на реальном счётчике.

## Out of scope (пока)

- Logs API (выгрузка визитов сырьём) — есть `references/logs-api.md` для ad-hoc вопросов, скрипта пока нет.
- Цели/конверсии — нужен `default_goal` в config; добавим когда понадобится.
- E-commerce.
- Сегменты.
