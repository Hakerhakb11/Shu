"""Абстракции (порты) слоя приложений для репозиториев и внешних клиентов."""

from abc import ABC, abstractmethod

from app.domain.models import CatalogItemSnapshot


class CartRepositoryInterface(ABC):
    """Интерфейс хранилища корзин пользователей."""

    @abstractmethod
    async def get_items(self, user_id: str) -> dict[int, int]:
        """Вернуть словарь {item_id: quantity} для корзины пользователя."""

    @abstractmethod
    async def get_item_quantity(self, user_id: str, item_id: int) -> int | None:
        """Вернуть текущее количество товара в корзине или None, если его нет."""

    @abstractmethod
    async def increment_item(self, user_id: str, item_id: int, delta: int) -> int:
        """Увеличить количество товара на delta и вернуть итоговое количество."""

    @abstractmethod
    async def set_item_quantity(self, user_id: str, item_id: int, quantity: int) -> int:
        """Установить точное количество товара и вернуть сохраненное значение."""

    @abstractmethod
    async def remove_item(self, user_id: str, item_id: int) -> bool:
        """Удалить позицию из корзины. Возвращает True, если позиция существовала."""

    @abstractmethod
    async def clear_cart(self, user_id: str) -> None:
        """Полностью очистить корзину пользователя."""

    @abstractmethod
    async def ping(self) -> bool:
        """Проверить доступность хранилища."""


class CatalogClientInterface(ABC):
    """Интерфейс клиента для взаимодействия с Catalog Service."""

    @abstractmethod
    async def get_items_batch(self, item_ids: list[int]) -> dict[int, CatalogItemSnapshot]:
        """Запросить актуальную информацию по списку ID книг пакетом."""
