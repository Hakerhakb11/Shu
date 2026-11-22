# Shu — маркетплейс книг

Shu — учебный микросервисный маркетплейс для покупки и продажи книг.

Проект разделяет систему на четыре компонента:

- API Gateway — единая точка входа и проверка JWT;
- Auth Service — регистрация, вход и управление сессиями;
- Catalog Service — каталог книг, поиск, категории и остатки;
- Cart Service — пользовательские корзины.

Взаимодействие сервисов реализуется по REST API. Для хранения данных используются PostgreSQL и Redis.

## Возможности

### Покупатель

- регистрация и вход;
- просмотр каталога книг;
- поиск и фильтрация;
- просмотр карточки книги;
- добавление книг в корзину;
- изменение количества товаров;
- оформление заказа в будущих версиях проекта.

### Продавец

- добавление книг;
- редактирование собственных товаров;
- снятие товаров с продажи;
- управление остатками.

### Модератор

- просмотр товаров на модерации;
- одобрение или отклонение товаров;
- блокировка и редактирование опубликованных товаров.

## Технологии

| Компонент | Технологии |
|---|---|
| API Gateway | Java, Spring Boot, Spring Cloud Gateway |
| Auth Service | Java, Spring Boot, PostgreSQL |
| Catalog Service | Python, FastAPI или Django REST Framework, PostgreSQL |
| Cart Service | Python, FastAPI или Django REST Framework, Redis |
| Общая инфраструктура | Docker Compose, Redis, PostgreSQL |
| Контракты API | OpenAPI |

## Структура репозитория

```text
shu/
├── contracts/
│   ├── auth/
│   ├── cart/
│   ├── catalog/
│   └── events/
├── docs/
├── services/
│   ├── api-gateway/
│   ├── auth-service/
│   ├── cart-service/
│   └── catalog-service/
├── docker-compose.yml
└── README.md
```

Подробное описание структуры находится в project-structure.md.

## Требования

Для запуска проекта необходимы:

- Git;
- Docker;
- Docker Compose;
- для локальной разработки сервисов — JDK и Python соответствующих версий.

## Запуск инфраструктуры

Из корня проекта выполните:

```bash
docker compose up -d
```

Проверить состояние контейнеров:

```bash
docker compose ps
```

В составе проекта запускаются:

| Компонент | Внешний порт |
|---|---:|
| Auth PostgreSQL | 5432 |
| Catalog PostgreSQL | 5433 |
| Cart PostgreSQL | 5434 |
| Redis | 6379 |

Остановить инфраструктуру:

```bash
docker compose down
```

Удалить контейнеры вместе с хранилищами данных:

```bash
docker compose down -v
```

Переменные для конфигурации берутся из файла`.env`.  
Скопировать конфигурацию из примера:
```bash
cp .env.example .env
```

## API

Каждый клиентский запрос проходит через API Gateway.

```text
Клиент → API Gateway → Auth Service
                    → Catalog Service
                    → Cart Service
```

Основные группы маршрутов:

```text
/auth/**     Auth Service
/catalog/**  Catalog Service
/cart/**     Cart Service
```

Контракты API планируется размещать в каталоге contracts:

- openapi.yaml;
- openapi.yaml;
- openapi.yaml;
- order-created.json.


## Лицензия
хз