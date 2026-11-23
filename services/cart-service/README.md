# Cart Service (Сервис Корзины)

Микросервис корзины для маркетплейса книг `Shu`. Реализован на FastAPI по принципам Чистой архитектуры (Clean Architecture) с хранением позиций в Redis и синхронизацией актуальных цен и остатков через `Catalog Service`.

## Архитектура проекта

```text
services/cart-service/
├── app/
│   ├── domain/             # Доменный слой: чистые сущности и бизнес-правила (чистый Python)
│   │   ├── models.py       # Cart, CartItem, CatalogItemSnapshot, CartItemQuantity, UnavailableReason
│   │   └── exceptions.py   # DomainError, ItemNotInCartError, CartLimitExceededError и др.
│   ├── application/        # Слой сценариев использования (Use Cases) и абстракций
│   │   ├── interfaces.py   # CartRepositoryInterface, CatalogClientInterface
│   │   └── services.py     # CartService
│   ├── infrastructure/     # Инфраструктурный слой: Redis и HTTP-клиент к каталогу
│   │   ├── cache/          # redis_client.py
│   │   ├── clients/        # catalog_client.py (POST /catalog/items/batch)
│   │   └── repositories/   # cart_repository.py (Redis Hash cart:{user_id})
│   ├── presentation/       # Слой представления HTTP (FastAPI, Pydantic DTOs)
│   │   ├── schemas.py      # Pydantic-схемы запросов и ответов
│   │   └── routers.py      # APIRouter (/cart, /cart/items, /health)
│   ├── core/               # Конфигурация, DI и глобальные обработчики ошибок
│   │   ├── config.py       # Pydantic Settings
│   │   ├── dependencies.py # Depends провайдеры и проверка X-User-Id
│   │   └── exceptions.py   # Маппинг DomainError -> ErrorResponse
│   └── main.py             # Точка входа FastAPI и lifespan
├── tests/                  # Модульные и интеграционные тесты (pytest, httpx)
├── Dockerfile              # Docker-образ сервиса
├── .env.example            # Пример переменных окружения
└── pyproject.toml          # Зависимости Poetry и конфиг Ruff/Pytest
```

## Хранение в Redis и связь с Catalog Service

- Каждая корзина хранится в Redis Hash под ключом `cart:{user_id}` (`field = item_id`, `value = quantity`) с автообновляемым TTL (по умолчанию 30 дней).
- При `GET /cart` сервис одним запросом `POST /catalog/items/batch` (`{"item_ids": [...]}`) запрашивает актуальные названия, цены, статусы и остатки в `catalog-service`.
- Если товар удалён (`DELETED`), снят с публикации (`NOT_APPROVED`), закончился (`OUT_OF_STOCK`) или его на складе меньше, чем в корзине (`INSUFFICIENT_STOCK`), позиция остаётся в ответе с `available: false` и полем `message`, но не входит в `total_price`.

## Эндпоинты API

Все ручки `/cart/**` требуют заголовок `X-User-Id` (пробрасывается `API Gateway`).

- `GET /cart` — получить корзину пользователя с актуальными ценами и доступностью.
- `POST /cart/items` — добавить товар или увеличить количество (`{"item_id": 42, "quantity": 1}`).
- `DELETE /cart/items/{item_id}?quantity=1` — уменьшить количество на `quantity` (если не передан — удалить позицию целиком).
- `DELETE /cart` — полностью очистить корзину (после оформления заказа).
- `GET /health` — проверка работоспособности сервиса и доступности Redis.

## Запуск и тестирование

```bash
# Установка зависимостей
poetry install

# Проверка стиля и форматирования
poetry run ruff check .
poetry run ruff format --check .

# Запуск тестов
poetry run pytest

# Запуск сервиса локально
cp .env.example .env
poetry run python -m app.main
```
