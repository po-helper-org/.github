# po-helper-org

> **Экосистема для роли AI Product Owner.**
> Автономный помощник для корпоративных руководителей, которые занимают
> позицию Product Owner и отвечают за продукты.

## Миссия

Сделать так, чтобы корпоративный руководитель в роли Product Owner делегировал
часть своих функций агентам и **предсказуемо достигал целей OKR** — с
надёжностью, за которую платят.

Удобство уровня Perplexity, Claude Code, Manus. Но, в отличие от универсальных
ассистентов, каждый компонент посвящён одному: **операционной эффективности
руководителей и команд**. Это не ещё один чат-бот — это операционка роли.

## Компоненты экосистемы

| Репозиторий | Роль |
|---|---|
| [po-helper](https://github.com/po-helper-org/po-helper) | AI-Native продуктовая операционка PO: multi-step пайплайны ИИ-агентов (OKR · Спринты · БФТ · Внешние запросы), онбординг PAF, методология Product Discovery |
| [gh-issue-agents](https://github.com/po-helper-org/gh-issue-agents) | Self-hosted Issue Agent Service — полный цикл Issue как durable Temporal-workflow (webhook + worker, GLM via z.ai) |
| [pr-agent-glm-setup](https://github.com/po-helper-org/pr-agent-glm-setup) | Готовый GitHub Actions конфиг: авто-CodeReview PR через PR-Agent (Qodo) + GLM |
| [po-helper-dev-closer](https://github.com/po-helper-org/po-helper-dev-closer) | _(заготовка)_ |

## Принципы

- **Надёжность прежде мощности** — делегируют только то, что воспроизводимо и наблюдаемо.
- **Процесс как код** — продуктовые практики выражены пайплайнами, а не ручными шагами.
- **Привязка к OKR** — ценность в движении к целям, не в объёме вывода.
- **Self-hosted first** — свои модели и инфраструктура, данные под контролем.
