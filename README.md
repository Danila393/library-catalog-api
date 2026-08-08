# Library Catalog API

Асинхронный REST API для управления библиотечным каталогом. Сервис поддерживает
CRUD-операции, поиск и пагинацию, хранит данные в PostgreSQL и автоматически
обогащает сведения о книгах через Open Library.

## Возможности

- создание, получение, частичное обновление и удаление книг;
- фильтрация по названию, автору, жанру, году и доступности;
- пагинация результатов;
- проверка бизнес-правил и уникальности ISBN;
- автоматическое обогащение обложкой, издателем, тематикой и рейтингом;
- асинхронная работа с PostgreSQL через SQLAlchemy 2 и `asyncpg`;
- миграции Alembic;
- retry с exponential backoff и circuit breaker для Open Library;
- JSON-логирование, request ID и access logs;
- Prometheus-метрики приложения и внешних запросов;
- Docker Compose для запуска API и PostgreSQL;
- unit- и API-тесты на pytest.

## Архитектура

Проект разделён на четыре основных слоя:

```text
API -> Domain <- Data
          ^
          |
       External
```

- `api` принимает HTTP-запросы, валидирует их и формирует ответы;
- `domain` содержит DTO, порты и бизнес-логику;
- `data` реализует работу с PostgreSQL;
- `external` реализует интеграцию с Open Library;
- `core` содержит конфигурацию, БД, логирование, метрики и обработку ошибок.

Domain не импортирует реализации API, Data или External. Реальные зависимости
собираются в `api/dependencies.py` через FastAPI Dependency Injection.

## Стек

- Python 3.11+ (Docker-образ использует Python 3.12);
- FastAPI и Uvicorn;
- PostgreSQL 16;
- SQLAlchemy 2, asyncpg и Alembic;
- Pydantic 2 и pydantic-settings;
- httpx, purgatory и prometheus-client;
- Poetry;
- pytest, Ruff, Black и mypy strict;
- Docker и Docker Compose.

## Быстрый запуск через Docker

### 1. Создайте `.env`

PowerShell:

```powershell
Copy-Item .env.example .env
```

Linux/macOS:

```bash
cp .env.example .env
```

Значения из `.env.example` предназначены для локальной разработки. Перед
публикацией приложения обязательно замените пароли и настройки окружения.

### 2. Соберите и запустите сервисы

```bash
docker compose up -d --build
```

При запуске контейнер приложения автоматически выполняет:

```bash
alembic upgrade head
```

После применения миграций запускается Uvicorn.

### 3. Проверьте контейнеры

```bash
docker compose ps
docker compose logs app
```

Оба контейнера должны иметь состояние `healthy`.

### 4. Откройте приложение

| Ресурс | URL |
|---|---|
| Корневой эндпоинт | <http://localhost:8000/> |
| Swagger UI | <http://localhost:8000/docs> |
| ReDoc | <http://localhost:8000/redoc> |
| Health-check | <http://localhost:8000/api/v1/health/> |
| Prometheus metrics | <http://localhost:8000/metrics/> |

Проверка из PowerShell:

```powershell
curl.exe http://localhost:8000/api/v1/health/
```

Остановка контейнеров без удаления данных PostgreSQL:

```bash
docker compose down
```

## Локальная разработка

Понадобятся Python 3.11 или новее, Poetry и Docker с Docker Compose.

### 1. Установите зависимости

```bash
poetry install
```

`pyproject.toml` и `poetry.lock` являются единственными источниками зависимостей
проекта.

### 2. Запустите PostgreSQL

```bash
docker compose up -d postgres
```

PostgreSQL слушает порт `5432` внутри Docker-сети и опубликован на порту `5433`
локального компьютера. Поэтому локальный `DATABASE_URL` использует
`localhost:5433`, а сервис `app` внутри Compose получает адрес `postgres:5432`.

### 3. Примените миграции

```bash
poetry run alembic upgrade head
poetry run alembic current
```

### 4. Запустите API

```bash
poetry run uvicorn library_catalog.main:app --app-dir src --reload
```

Параметр `--app-dir src` нужен из-за структуры проекта `src/library_catalog`.

## API

Базовый префикс API: `/api/v1`.

| Метод | Путь | Назначение | Успешный код |
|---|---|---|---:|
| `POST` | `/api/v1/books/` | Создать книгу | `201` |
| `GET` | `/api/v1/books/` | Получить список книг | `200` |
| `GET` | `/api/v1/books/{book_id}` | Получить книгу | `200` |
| `PATCH` | `/api/v1/books/{book_id}` | Частично обновить книгу | `200` |
| `DELETE` | `/api/v1/books/{book_id}` | Удалить книгу | `204` |
| `GET` | `/api/v1/health/` | Проверить API и БД | `200` или `503` |

### Поиск и пагинация

`GET /api/v1/books/` принимает параметры:

- `title` — частичное регистронезависимое совпадение;
- `author` — частичное регистронезависимое совпадение;
- `genre` — точное совпадение;
- `year` — точное совпадение;
- `available` — фильтр `true`/`false`;
- `page` — номер страницы, начиная с 1;
- `page_size` — количество элементов от 1 до 100.

Для поиска по названию и автору в PostgreSQL используются GIN trigram indexes.

### Основные ошибки

| Код | Значение |
|---:|---|
| `400` | Нарушено бизнес-правило |
| `404` | Книга не найдена |
| `409` | Книга с таким ISBN уже существует |
| `422` | Запрос не прошёл Pydantic-валидацию |
| `503` | База данных недоступна на health-check |
| `500` | Непредвиденная внутренняя ошибка |

Каждый HTTP-ответ содержит заголовок `X-Request-ID`. Его значение также
добавляется в логи, что позволяет связать запрос с конкретными записями журнала.

## Open Library и отказоустойчивость

При создании книги приложение пытается получить дополнительные данные из Open
Library. Недоступность внешнего API не блокирует сохранение базовой информации.

Для внешних запросов настроены:

- timeout;
- ограничение HTTP connection pool;
- retry с exponential backoff;
- circuit breaker;
- счётчик результатов и histogram длительности запросов.

Порог circuit breaker и время восстановления задаются переменными:

```text
OPENLIBRARY_CIRCUIT_BREAKER_FAILURE_THRESHOLD
OPENLIBRARY_CIRCUIT_BREAKER_RECOVERY_TIMEOUT
```

## Метрики и логирование

Prometheus-метрики доступны на `/metrics/`. Основные метрики внешнего API:

```text
library_catalog_external_api_requests_total
library_catalog_external_api_request_duration_seconds
```

Формат логов задаётся через `LOG_FORMAT`:

- `text` — удобен для локальной разработки;
- `json` — подходит для централизованного сбора логов.

## Миграции

Проверить текущую миграцию:

```bash
poetry run alembic current
```

Применить все миграции:

```bash
poetry run alembic upgrade head
```

Создать миграцию после изменения моделей:

```bash
poetry run alembic revision --autogenerate -m "describe change"
```

Перед коммитом новой миграции обязательно проверьте её `upgrade()` и
`downgrade()` вручную.

## Проверка качества и тесты

```bash
poetry run python -m black --check src tests
poetry run python -m ruff check .
poetry run python -m mypy --no-incremental
poetry run python -m pytest
poetry check
```

Тесты включают:

- бизнес-правила `BookService`;
- обработку конфликтов ISBN в репозитории;
- CRUD-контракты и валидацию API;
- health-check при доступной и недоступной БД;
- проверку graceful degradation при таймауте Open Library.

## Конфигурация

Полный пример находится в `.env.example`. Основные группы настроек:

- приложение: `ENVIRONMENT`, `DEBUG`, `API_V1_PREFIX`, `CORS_ORIGINS`;
- PostgreSQL: `POSTGRES_*`, `DATABASE_URL`, `DATABASE_POOL_*`;
- Open Library: `OPENLIBRARY_*`;
- логирование: `LOG_LEVEL`, `LOG_FORMAT`.

Настройки читаются через `pydantic-settings`. Не добавляйте настоящий `.env` и
секреты в Git.

## Ограничения

- JWT-аутентификация и роли не входят в обязательную часть задания, поэтому
  эндпоинты каталога сейчас публичные;
- Redis-кеширование и фоновое обогащение данных не реализованы;
- TLS, HSTS и ограничение доступа к `/docs` и `/metrics/` должны настраиваться
  на reverse proxy или ingress перед production-развёртыванием;
- стандартная конфигурация CORS предназначена для разработки и должна быть
  ограничена конкретными origins в production.
