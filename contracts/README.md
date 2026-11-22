# Shu API Contracts & Documentation Server

Контракты API и схемы событий для всех микросервисов книжного маркетплейса `Shu`.

## Структура контрактов

```text
contracts/
├── Dockerfile                   # Docker-образ Swagger UI
├── .dockerignore
├── auth/
│   └── openapi.yaml             # Спецификация Auth Service API
├── cart/
│   └── openapi.yaml             # Спецификация Cart Service API
├── catalog/
│   └── openapi.yaml             # Спецификация Catalog Service API
└── events/
    └── order-created.json       # JSON-схема события создания заказа
```

## Запуск в Docker

### Через Docker CLI
```bash
cd contracts
docker build -t shu-contracts .
docker run -d -p 8085:8080 --name shu-contracts shu-contracts
```

### Через Docker Compose
Сервис доступен в общем `docker-compose.yml`:
```bash
docker compose up -d contracts
```

## Доступ к документации и схемам

- **Интерактивный Swagger UI**: [http://localhost:8085](http://localhost:8085)  
  В выпадающем списке сверху доступны для выбора:
  - `Catalog Service API`
  - `Auth Service API`
  - `Cart Service API`
- **Прямой доступ к сырым файлам спецификаций**:
  - Каталог: `http://localhost:8085/contracts/catalog/openapi.yaml`
  - Авторизация: `http://localhost:8085/contracts/auth/openapi.yaml`
  - Корзина: `http://localhost:8085/contracts/cart/openapi.yaml`
  - Событие заказа: `http://localhost:8085/contracts/events/order-created.json`
