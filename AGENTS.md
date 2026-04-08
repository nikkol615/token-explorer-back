# SolExplorer - Cursor AI Agent Guidelines

## 🎯 Описание проекта (Project Context)
SolExplorer — это веб-приложение для анализа токенов в сети Solana. 
Пользователь вводит адрес (Mint Address) смарт-контракта токена, а приложение собирает, агрегирует и анализирует данные о нём, отображая информацию в удобном виде (Token Card, DEX Pools, Scoring).

## 🛠 Технологический стек и Актуальные библиотеки
**Backend (Python 3.11+):**
- **Framework:** `fastapi` (веб-фреймворк) + `uvicorn` (сервер).
- **Validation & Config:** `pydantic` v2, `pydantic-settings`.
- **HTTP Client:** `httpx` (для асинхронных запросов к внешним API).
- **Solana Core:** `solders` (актуальная замена устаревшим типам `solana-py` — используем `solders.pubkey.Pubkey` для валидации адресов).
- **Data Source:** DexScreener API (`https://api.dexscreener.com/latest/dex/tokens/{token_address}`) + опционально Jupiter/BirdEye API.

**Frontend (будет добавлен позже):**
- **Framework:** React + Vite (TS/JS) или Vue 3.
- **Styling:** Tailwind CSS.
- **HTTP Client:** `axios` или `fetch`.

---

## 📁 Архитектура и Структура (Project Structure)
Текущая структура бэкенда:
```text
.
├── poetry.lock / pyproject.toml # Управление зависимостями
└── solexplorer
    ├── __init__.py
    ├── analyse          # Бизнес-логика скоринга и оценки токена
    │   └── get_score.py
    ├── api              # Роуты FastAPI
    │   └── v1
    │       ├── router.py
    │       └── token_analyse.py
    ├── config           # Конфигурация (Pydantic BaseSettings)
    │   ├── app.py
    │   └── solana.py
    ├── main.py          # Точка входа, инициализация FastAPI
    └── solana           # Взаимодействие с блокчейном и внешними API
        └── get_token.py
```

---

## 📏 Правила написания кода (Coding Standards)

### 1. Стиль именования (Naming Conventions)
- **Файлы и директории (Python):** `snake_case.py` (например, `token_analyse.py`).
- **Классы (Python):** `PascalCase` (например, `TokenScore`, `DexPoolModel`).
- **Функции и переменные (Python):** `snake_case` (например, `get_token_data`, `total_liquidity`).
- **Файлы (Frontend):** `PascalCase.tsx` для React-компонентов, `kebab-case.ts` для утилит.

### 2. Типизация и Документация (Typing & Docstrings)
- **Strict Typing:** Весь Python код должен иметь строгие аннотации типов (Type Hints). Используйте `dict`, `list`, `Optional`, `Any` из модуля `typing` (или встроенные типы в Python 3.10+).
- **Pydantic Models:** Входящие запросы и исходящие ответы FastAPI ДОЛЖНЫ быть описаны через модели Pydantic. Возвращать сырые словари (`dict`) из эндпоинтов запрещено.
- **Docstrings:** Каждая функция и класс должны иметь Google Style Docstring с описанием аргументов и возвращаемого значения.

### 3. Обработка ошибок (Error Handling)
- **Валидация адреса:** Перед отправкой запросов проверяйте валидность Solana-адреса с помощью `solders.pubkey.Pubkey.from_string(address)`. При ошибке отдавать `HTTPException(status_code=400, detail="Invalid Solana address")`.
- **Внешние API:** Обрабатывайте таймауты и ошибки `httpx`. Если API недоступен, возвращайте `HTTPException(status_code=503, detail="External API unavailable")`.
- **Токен не найден:** Если API возвращает пустой список пулов, отдавать `HTTPException(status_code=404, detail="Token not found or has no liquidity pools")`.

### 4. Модульность (Modularity Rules)
- **Zero Fat Controllers:** В файлах роутеров (`api/v1/token_analyse.py`) не должно быть сложной бизнес-логики. Они должны только принимать запрос, вызывать сервисные функции из `solana/` и `analyse/` и возвращать ответ.
- Все HTTP-вызовы (к DexScreener) должны находиться в `solana/get_token.py` (или аналогичных файлах-клиентах).
- Вся логика подсчета баллов должна быть инкапсулирована строго в `analyse/get_score.py`.

---

## 🧠 Core Logic Guidelines: Скоринг токена (Token Scoring System)
Агент, когда будешь писать функцию `calculate_score` в `analyse/get_score.py`, реализуй следующую логику оценки (от 0 до 100 баллов, где <40 это 🔴, 40-70 это 🟡, >70 это 🟢):

1. **Количество DEX (Max 20 pts):** Торгуется ли токен на нескольких DEX (Raydium, Orca, Meteora)? 1 DEX - 10 pts, >= 2 DEX - 20 pts.
2. **Общая ликвидность (Max 30 pts):** <$10k (0 pts), $10k-$50k (10 pts), $50k-$200k (20 pts), >$200k (30 pts).
3. **Объем/Ликвидность Ratio (Max 20 pts):** Нормальный показатель (например, 0.1 - 5.0) получает высокий балл. Слишком низкий (мертвый) или слишком высокий (wash trading) штрафуются.
4. **Концентрация ликвидности (Max 20 pts):** Доля главного пула (Top Pool). Если >95% в одном пуле - 5 pts, если ликвидность распределена (Top pool <80%) - 20 pts.
5. **Возраст пулов (Max 10 pts):** < 1 часа (0 pts), 1-24 часа (5 pts), > 24 часов (10 pts) (вычисляется из `pairCreatedAt` от DexScreener).

Ответ системы скоринга должен быть структурированным:
```json
{
  "total_score": 85,
  "status_emoji": "🟢",
  "breakdown":[
    {"criterion": "Liquidity", "points": 30, "max_points": 30, "reason": "Total liquidity > $200k"},
    {"criterion": "DEX Count", "points": 10, "max_points": 20, "reason": "Trading on 1 DEX(es)"}
  ]
}
```

---

## 🤖 Instructions for AI (System Prompts)
When completing tasks in this project, follow these steps:
1. **Analyze:** Read the relevant configuration and existing models before creating new files.
2. **Implement Backend:** 
   - Add models to a new `models/` or `schemas/` directory if needed.
   - Use `httpx.AsyncClient` for fetching data from `https://api.dexscreener.com/latest/dex/tokens/{address}`.
   - Aggregate the DexScreener JSON into standard Pydantic responses.
   - Implement the scoring logic.
3. **Review Check:** Make sure imports are absolute where applicable (`from solexplorer.config import ...`), code is async where needed, and error handling wraps external calls.