# Стандарт: LLM только через профиль Hermes (ADR 0016)

Действует для всех репозиториев po-helper-org. Правило одно: **ни один сервис не обращается
к LLM-провайдеру (Z.AI/GLM, OpenAI, Anthropic, Requesty, …) напрямую** — только через целевой
профиль Hermes. Это решение зафиксировано в ADR 0016 (репозиторий poh-hermes-bridge,
`docs/adr/0016-llm-tolko-cherez-hermes.md`, принят 03.11.2026) и закрепляется CI-проверкой,
которая падает на прямых вызовах.

Зачем: расход токенов виден по профилю/сервису/фиче, квота Z.AI не «выбирается неожиданно»
(кейс 02.11 — исчерпание недельного лимита вслепую), ключи лежат в одном месте и ротируются
одной операцией.

## Правило

1. **Единственный вход к LLM — API-сервер шлюза Hermes**: `http://127.0.0.1:8642/p/<profile>/v1/…`
   (`/runs` — долгие ходы агента, `/responses` или `/chat/completions` — генерация/стрим).
2. **Один сервис = один целевой профиль.** Смена модели — в конфиге профиля, не в коде сервиса.
   Новый сервис → сначала профиль, потом код.
3. **Каждый запрос несёт метку фичи** — заголовок `X-Hermes-Feature: <service>/<feature>`
   (например `poh-widget-inbox/notechat`); после вызова — строка `llm-usage …` в stdout (journald).
4. **Ключи провайдеров в коде и конфигах репозиториев запрещены** — ключ профиля в файле
   `~/.config/<svc>/…` (600) или env развёртывания.
5. **CI-проверка обязательна** (настройка ниже): коммит/PR с прямым вызовом провайдера
   (адрес хоста провайдера или импорт SDK `openai`/`anthropic`) роняет сборку.

## CI-проверка в репозитории

Канонический скрипт: [scripts/check-llm-direct.sh](scripts/check-llm-direct.sh) (этот репозиторий).
В сервисном репозитории — вендор-копия `scripts/check-llm-direct.sh` + workflow:

```yaml
# .github/workflows/llm-direct-check.yml
name: llm-direct-check
on:
  push: { branches: [main] }
  pull_request:
permissions:
  contents: read
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: scripts/check-llm-direct.sh
```

Обновление стандарта → обновить канон и синхронно перезалить вендор-копии
(копия нужна, потому что reusable workflow из приватного репо недоступен приватным
репозиториям через `GITHUB_TOKEN`; скрипт один и тот же, расходится только путь).

## Исключения

Осознанные исключения фиксируются в репозитории и ревьюятся в PR — либо строкой в
`.github/llm-direct-allow.txt` (формат: `path/файл # причина`), либо inline-маркером
`llm-direct: allow` в комментарии рядом со строкой. Причина обязательна. Примеры
легитимных причин: откат на прямой вызов (классы `Zai*` до ADR 0016), фикстуры тестов
(строки логов с URL провайдера), голосовая транскрипция Requesty (решение PO по ADR 0016 §4),
транспорт пилота agentgateway (остаётся транспортом внутри профиля, не входной точкой).

Исключения не длятся вечно: откатные классы удаляются, когда migration приживётся,
строка исключения — вместе с ними.

## Как подключить новый сервис

1. **Профиль**: создать целевой профиль Hermes (`hermes profile add <service>-ai`), выбрать
   модель и пул ключей в конфиге профиля. Имя — по сервису: `poh-foo-bar` → профиль `foo-bar-ai`
   (или из таблицы ADR 0016 §5, если сервис уже там).
2. **Ключ сервиса**: `~/.config/<svc>/<svc>-key` (chmod 600) — значение `API_SERVER_KEY` профиля.
3. **Клиент**: HTTP-вызовы на `http://127.0.0.1:8642/p/<profile>/v1/responses` (или `/runs`,
   или `/chat/completions` для OpenAI-совместимого клиента) с заголовками
   `Authorization: Bearer <ключ>` и `X-Hermes-Feature: <service>/<feature>`.
   SDK OpenAI допустим, если `base_url` указывает на профиль (пример — poh-issue-agents:
   `ZAI_BASE_URL=http://127.0.0.1:8642/p/issue-agents/v1`, заголовок ставится кодом).
4. **Usage**: после каждого вызова печатать `llm-usage service=<svc> feature=<f> profile=<p>
   model=<m> input_tokens=<N> output_tokens=<N> cache_read_tokens=<N>` в stdout → journald.
5. **CI**: положить вендор-копию скрипта и workflow (блок выше), прогнать локально
   `scripts/check-llm-direct.sh` — должен быть зелёный. Прямые адреса провайдеров в коде
   и конфигах — убрать; легитимный остаток — в allowlist с причиной.

## Реестр «сервис → профиль»

Живёт в ADR 0016 §5 (таблица миграции) и поддерживается владельцем; после завершения
миграции ревизии таблицы — в PR к ADR. Текущее соответствие (2026-11-05):

| Сервис | Профиль | Фичи (X-Hermes-Feature) |
|---|---|---|
| poh-widget-inbox | inbox-ai | notechat, consultation; transcribe — Requesty напрямую (решение PO, allowlist) |
| poh-sprint-agent | sprint-agent-ai | daily |
| poh-tg-mrs-tasks | po-mrs | extract |
| poh-hermes-bridge | inbox-plan | plan-chat |
| poh-bft-box | bft-ai | iteration |
| poh-issue-agents (+копия в poh-harness skills) | issue-agents | extract |

## Контроль

- CI (этот скрипт) — на push в main и каждый PR.
- llm-exporter (poh-observability) — расход по профилю/сервису/фиче из state.db + journald `llm-usage`.
- Ротация ключей — только через `.env` профилей Hermes; обнаруженный в репозитории ключ — ротация.
