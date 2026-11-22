# Auth Service

Auth Service реализован по Clean Architecture и предоставляет API регистрации, входа, обновления и выхода из сессии.

## Запуск

Из корня проекта:

```bash
docker compose up -d auth-postgres redis auth
```

Локально с уже запущенными PostgreSQL и Redis:

```bash
cd services/auth-service
mvn spring-boot:run
```

## Конфигурация

- `AUTH_DB_URL` — JDBC URL PostgreSQL;
- `AUTH_DB_USER`, `AUTH_DB_PASSWORD` — учетные данные БД;
- `REDIS_HOST`, `REDIS_PORT` — Redis для blacklist access-токенов;
- `AUTH_ACCESS_TTL_SECONDS` — срок access-токена (по умолчанию 900);
- `AUTH_REFRESH_TTL_DAYS` — срок refresh-сессии (по умолчанию 30);
- `AUTH_COOKIE_SECURE` — флаг Secure для refresh cookie;
- `AUTH_JWT_PRIVATE_KEY_PEM` — RSA private key в PKCS#8 PEM;
- `AUTH_JWT_PUBLIC_KEY_PEM` — RSA public key в X.509 PEM.

Если RSA-ключи не заданы, сервис создает пару ключей при запуске. Для нескольких экземпляров сервиса ключи необходимо передавать из внешнего конфигурационного хранилища.

## API

Контракт: `contracts/auth/openapi.yaml`.

- `POST /auth/register`;
- `POST /auth/login`;
- `POST /auth/refresh`;
- `POST /auth/logout`.

Refresh-токен передается в HttpOnly cookie `refreshToken` и хранится в PostgreSQL только в виде SHA-256 хэша.

Ответственность:

- регистрация;
- вход;
- logout;
- обновление токена;
- хранение учетных записей;
- хэширование паролей;
- выдача JWT-токенов;
- управление ролями.

Основные таблицы PostgreSQL:

```text
users
roles
user_roles
refresh_tokens
```

Роли:

```text
CLIENT
SELLER
MODERATOR
ADMIN
COURIER
```

Состав роли может расширяться по мере реализации проекта.

При входе возвращаются:

- access-токен с коротким сроком жизни;
- refresh-токен в HttpOnly cookie.

Refresh-токены должны храниться в защищенном виде с возможностью отзыва.
