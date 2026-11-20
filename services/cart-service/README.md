# Catalog Service

Управляет товарами маркетплейса.

Основные сущности:

```text
Book
Category
Author
Publisher
Stock
ProductStatus
```

Ответственность:

- публичный просмотр книг;
- поиск по названиям;
- фильтрация;
- пагинация;
- категории;
- остатки;
- создание товаров продавцами;
- редактирование товара;
- модерация;
- кэширование популярных запросов;
- пакетное получение товаров для корзины.

Предполагаемые endpoints:

```text
GET    /catalog/items
GET    /catalog/items/{id}
POST   /catalog/items
PUT    /catalog/items/{id}
DELETE /catalog/items/{id}
POST   /catalog/items/batch
GET    /catalog/moderation/items
PATCH  /catalog/items/{id}/status
```

Статусы товаров:

```text
DRAFT
PENDING
APPROVED
REJECTED
BLOCKED
```

Поиск может использовать PostgreSQL full-text search:

- поля `title` и `description`;
- `tsvector`;
- GIN-индекс;
- опционально `pg_trgm` для поиска с опечатками.

Redis используется для кэширования карточек товаров и результатов популярных запросов.