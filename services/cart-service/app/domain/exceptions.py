"""Доменные исключения сервиса корзины."""


class DomainError(Exception):
    """Базовое доменное исключение с машиночитаемым кодом ошибки."""

    error_code: str = "DOMAIN_ERROR"

    def __init__(self, message: str, error_code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if error_code is not None:
            self.error_code = error_code


class UnauthorizedUserError(DomainError):
    """Отсутствует или невалиден идентификатор пользователя (X-User-Id)."""

    error_code = "UNAUTHORIZED"


class InvalidCartOperationError(DomainError):
    """Некорректные параметры операции с корзиной."""

    error_code = "INVALID_CART_OPERATION"


class CartLimitExceededError(InvalidCartOperationError):
    """Превышено максимально допустимое количество одного товара в корзине."""

    error_code = "CART_LIMIT_EXCEEDED"


class ItemNotInCartError(DomainError):
    """Запрошенный товар отсутствует в корзине пользователя."""

    error_code = "ITEM_NOT_IN_CART"

    def __init__(self, item_id: int) -> None:
        super().__init__(
            message=f"Товар с ID {item_id} не найден в корзине",
            error_code=self.error_code,
        )
        self.item_id = item_id


class CatalogServiceUnavailableError(DomainError):
    """Сервис каталога временно недоступен или вернул некорректный ответ."""

    error_code = "CATALOG_SERVICE_UNAVAILABLE"


class CartStorageUnavailableError(DomainError):
    """Хранилище корзин (Redis) временно недоступно."""

    error_code = "CART_STORAGE_UNAVAILABLE"
