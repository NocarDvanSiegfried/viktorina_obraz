# viktorina_obraz

MVP веб-сервиса для хакатона **«ИИ для образования: автоматизация рутинных задач»**.  
Проект помогает учителю быстро превращать учебный материал в готовую викторину с генерацией, редактированием, прохождением и экспортом.

## Что это за проект

`viktorina_obraz` — это система с тремя основными режимами:

- **Создание**: генерация викторины из текста или файла через LLM.
- **Проведение**: ученик проходит викторину по персональной ссылке.
- **Аналитика и доработка**: учитель видит результаты, правит вопросы, сохраняет версии и экспортирует материалы.

Проект соответствует артефактам и критериям кейса:

- рабочий MVP веб-сервиса;
- полный воспроизводимый сценарий;
- код с инструкцией запуска;
- поддержка требуемых форматов и экспортов;
- ограничения запросов к LLM и изоляция данных по `owner_id`.

## Что уже сделано

### Генерация и обработка материалов

- Генерация викторины через GigaChat из:
  - текста;
  - `.txt`, `.pdf`, `.docx`, `.pptx`;
  - изображений (через vision-модель).
- Поддержка типов вопросов:
  - `single_choice`,
  - `multiple_choice`,
  - `true_false`.
- Настройка сложности и количества вопросов.

### Редактирование и версияция

- Редактирование вопросов и настроек викторины.
- Пересоздание отдельного вопроса через ИИ.
- Лимит до 15 вопросов.
- История версий викторины:
  - список версий;
  - просмотр снимка;
  - восстановление.
- Каталог источников (`source_fragment`) с preview.

### Прохождение и результаты

- Полный ученический сценарий:
  - `start -> questions -> answer -> finish`.
- Таймеры, попытки, подсчет баллов.
- Страница результатов:
  - проценты,
  - ошибки,
  - агрегаты по классу.
- Режим учителя с пошаговым показом и fullscreen.

### Форматы вывода и экспорт

- Экспорт в:
  - `PDF`,
  - `DOCX`,
  - `PPTX` (включая режим для класса без ответов).
- Быстрый просмотр перед отправкой ученикам.

### Безопасность и устойчивость MVP

- Изоляция данных по `owner_id` (доступ только к своим викторинам).
- Rate limit генерации на пользователя (429).
- Скрипты проверки секретов, env и readiness деплоя.

## Технологический стек

- **Backend**: `FastAPI`, `SQLAlchemy`, `SQLite`, `python-docx`, `fpdf`, `python-pptx`
- **Frontend**: `React`, `TypeScript`, `Vite`, `React Router`
- **Тесты**: `pytest`, `Playwright`
- **Деплой**: `Docker`, `docker compose`, `nginx`

## Архитектура (вкратце)

- `frontend` (SPA) обращается к API backend.
- `backend`:
  - принимает материал,
  - подготавливает фрагменты,
  - вызывает LLM,
  - сохраняет викторину/вопросы/результаты в БД.
- Экспорт формируется на backend и отдается как файл.

Подробнее: `docs/ARCHITECTURE.md`.

## Пользовательский путь (полный сценарий)

1. Учитель открывает `/create`.
2. Вставляет текст или загружает файл.
3. ИИ генерирует викторину.
4. Учитель смотрит **быстрый просмотр** и при необходимости редактирует.
5. Отправляет ссылку ученикам.
6. Ученики проходят `/student/:id`.
7. Учитель анализирует `/results/:id`.
8. При необходимости экспортирует материалы (`PDF`, `DOCX`, `PPTX`) и обновляет викторину.

## Быстрый локальный запуск

### 1) Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Проверка:

- Health: `http://localhost:8000/health`
- Swagger: `http://localhost:8000/docs`

### 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

Открыть: `http://localhost:5173`

## Запуск в Docker

```bash
docker compose build
docker compose up
```

- UI: `http://localhost:8080`
- API: `http://localhost:8000/health`

## Production / сервер

Пошагово и под шаблоны:

- `docs/DEPLOY.md`
- `docs/PROD_CHECKLIST.md`

Ключевые файлы-шаблоны:

- `.env.production.example`
- `backend/.env.production.example`
- `frontend/.env.production.example`

Команда деплоя:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
```

## Переменные окружения

Основное:

- Backend: `backend/.env.example`
- Production backend: `backend/.env.production.example`
- Frontend: `frontend/.env.example`
- Production frontend: `frontend/.env.production.example`

Ключевые backend-переменные:

- `GIGACHAT_AUTH_KEY`
- `GIGACHAT_SCOPE`
- `GIGACHAT_MODEL`
- `GIGACHAT_VISION_MODEL`
- `GIGACHAT_CA_BUNDLE_FILE`
- `FRONTEND_ORIGIN`
- `DATABASE_URL`
- `QUIZ_GENERATE_RATE_LIMIT_MAX_REQUESTS`
- `QUIZ_GENERATE_RATE_LIMIT_WINDOW_SECONDS`

## Тесты и качество

### Backend

```bash
cd backend
pytest
```

### Frontend build

```bash
cd frontend
npm run build
```

### E2E

```bash
npm install
npx playwright install chromium
npm run test:e2e
```

Дополнительно:

- prod smoke: `npm run test:e2e:prod`
- финальный gate: `npm run gate:final`

## Важные маршруты UI

- `/` — список викторин
- `/create` — создание
- `/edit/:id` — редактирование и быстрый просмотр
- `/student/:id` — прохождение учеником
- `/results/:id` — результаты
- `/teacher/:id` — режим учителя

## Документация

- `docs/ARCHITECTURE.md` — архитектура
- `docs/DEPLOY.md` — деплой
- `docs/PROD_CHECKLIST.md` — прод-чеклист
- `docs/LIVE_VERIFICATION.md` — live-проверки LLM
- `docs/PRIVACY.md` — приватность
- `docs/UX_ACCEPTANCE.md` — UX-критерии

## Структура репозитория

- `backend/app/` — API, сервисы, модели
- `backend/tests/` — unit/integration tests
- `frontend/src/` — клиентский интерфейс
- `e2e/tests/` — end-to-end сценарии
- `scripts/` — readiness/health/secrets скрипты
- `docs/` — материалы проекта и хакатона

