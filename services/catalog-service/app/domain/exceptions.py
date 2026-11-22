"""Domain exceptions (pure Python, framework independent)."""


class DomainError(Exception):
    """Base domain exception."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class EntityNotFoundError(DomainError):
    """Base entity not found exception."""


class ItemNotFoundError(EntityNotFoundError):
    """Raised when an item is not found."""

    def __init__(self, item_id: int) -> None:
        super().__init__(f"Товар с id {item_id} не найден.")
        self.item_id = item_id


class CategoryNotFoundError(EntityNotFoundError):
    """Raised when a category is not found."""

    def __init__(self, category_id: int) -> None:
        super().__init__(f"Категория с id {category_id} не найдена.")
        self.category_id = category_id


class PermissionDeniedError(DomainError):
    """Raised when a user has insufficient permissions to perform an action."""

    def __init__(self, message: str = "Недостаточно прав для выполнения действия.") -> None:
        super().__init__(message)


class InvalidOperationError(DomainError):
    """Raised when a domain operation is invalid."""
