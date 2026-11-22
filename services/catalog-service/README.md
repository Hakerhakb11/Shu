# Catalog Service (Сервис Каталога Книг)

Микросервис каталога для C2C маркетплейса книг (аналог Авито). Реализован на FastAPI с соблюдением принципов Чистой архитектуры (Clean Architecture), базы данных PostgreSQL и кэширования в Redis.

## Архитектура проекта

Код строго структурирован по слоям в соответствии с правилами Clean Architecture:

```text
services/catalog-service/
├── app/
│   ├── domain/             # Доменный слой: чистые сущности, value-объекты, бизнес-правила (чистый Python)
│   │   ├── models.py       # Item, Category, ItemCharacteristic, ItemStock, ItemStatus, UserRole
│   │   └── exceptions.py   # DomainError, ItemNotFoundError, PermissionDeniedError, etc.
│   ├── application/        # Слой сценариев использования (Use Cases) и абстракций
│   │   ├── interfaces.py   # ItemRepositoryInterface, CategoryRepositoryInterface, CacheServiceInterface
│   │   └── services.py     # CatalogService (оркестрация бизнес-логики, работа с кэшем, права доступа)
│   ├── infrastructure/     # Инфраструктурный слой: внешние зависимости
│   │   ├── db/             # SQLAlchemy модели, управление сессиями, PostgreSQL индексы
│   │   ├── cache/          # Redis клиент (RedisCacheService), сериализация/десериализация, TTL
│   │   └── repositories/   # ItemRepository, CategoryRepository (маппинг моделей в Domain)
│   ├── presentation/       # Слой представления HTTP (FastAPI, Pydantic DTOs)
│   │   ├── schemas.py      # Pydantic схемы запросов и ответов
│   │   └── routers.py      # APIRouter (/catalog/items, /catalog/categories, /catalog/moderation)
│   ├── core/               # Конфигурация, Dependency Injection, глобальные обработчики ошибок
│   │   ├── config.py       # Pydantic Settings
│   │   ├── dependencies.py # DI провайдеры сессий, репозиториев, ролевой проверки
│   │   └── exceptions.py   # Маппинг доменных исключений в HTTP коды
│   └── main.py             # Точка входа FastAPI приложения
├── migrations/             # Alembic миграции (GIN индексы, tsvector, pg_trgm)
├── tests/                  # Модульные и интеграционные тесты (pytest, httpx, aiosqlite)
├── Dockerfile              # Docker образ
└── pyproject.toml          # Зависимости Poetry
```

## Ролевая модель и проверка прав

Gateway пробрасывает заголовки `X-User-Id` и `X-User-Role`:
- `CLIENT` (Покупатель) — доступ только к публичным ручкам каталога. Попытка создать/изменить/удалить товар или зайти в модерацию возвращает `403 Forbidden`.
- `SELLER` (Продавец) — может создавать товары (`POST /catalog/items`), редактировать и удалять **только свои** товары (`PUT /catalog/items/{id}`, `DELETE /catalog/items/{id}`). При создании товар получает статус `PENDING`.
- `MODERATOR` (Модератор) — имеет право просматривать очередь модерации (`GET /catalog/moderation/items`), одобрять или отклонять товары (`PATCH /catalog/items/{id}/status`), а также редактировать и удалять чужие товары при нарушениях.

## Эндпоинты API

### Публичные ручки
- `GET /catalog/items` — список опубликованных (`APPROVED`) товаров с пагинацией (`page`, `size`), фильтрами (`category_id`, `min_price`, `max_price`) и поиском (`search`).
- `GET /catalog/items/{id}` — подробная карточка товара (характеристики, остаток, категория). Сначала читается из Redis; при отсутствии читается из PostgreSQL и сохраняется в Redis на 2 минуты.
- `POST /catalog/items/batch` — пакетное получение товаров по списку ID (для Сервиса Корзины, с флагом доступности `available`).
- `GET /catalog/categories` — список категорий книг.
- `GET /health` — проверка работоспособности сервиса.

### Ручки Продавца
- `POST /catalog/items` — создание товара (`X-User-Role: SELLER`, `X-User-Id`). Статус: `PENDING`.
- `PUT /catalog/items/{id}` — редактирование своего товара (сбрасывает кэш в Redis).
- `DELETE /catalog/items/{id}` — удаление своего товара (сбрасывает кэш в Redis).

### Ручки Модератора
- `GET /catalog/moderation/items` — список товаров, ожидающих проверки (`status=PENDING`). Требует `X-User-Role: MODERATOR`.
- `PATCH /catalog/items/{id}/status` — изменение статуса (`APPROVED`, `REJECTED`, `BLOCKED`). Требует `X-User-Role: MODERATOR`. Сбрасывает кэш в Redis.
- `PUT /catalog/items/{id}` — редактирование любого товара модератором.
- `DELETE /catalog/items/{id}` — удаление любого товара модератором.

## Полнотекстовый поиск PostgreSQL

В миграциях Alembic настраиваются:
1. `tsvector` с русским словарем (`russian`) по полям `title`, `author`, `description` с GIN-индексом `idx_items_fts_gin`.
2. Расширение `pg_trgm` и GIN триграмм-индекс `idx_items_title_trgm` по названию книги для нечеткого поиска и опечаток.

## Запуск и тестирование

```bash
# Установка зависимостей
poetry install

# Проверка стиля кода
poetry run ruff check .
poetry run ruff format --check .

# Запуск тестов
poetry run pytest

# Запуск сервера разработки
poetry run python -m app.main
```
