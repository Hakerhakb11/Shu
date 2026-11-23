"""HTTP-клиент для пакетного получения товаров из Catalog Service."""

from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

from app.application.interfaces import CatalogClientInterface
from app.domain.exceptions import CatalogServiceUnavailableError
from app.domain.models import CatalogItemSnapshot


class HttpCatalogClient(CatalogClientInterface):
    """Реализация клиента Catalog Service через httpx.AsyncClient."""

    BATCH_ENDPOINT = "/catalog/items/batch"

    def __init__(self, http_client: httpx.AsyncClient) -> None:
        self._http_client = http_client

    async def get_items_batch(self, item_ids: list[int]) -> dict[int, CatalogItemSnapshot]:
        """Выполнить POST /catalog/items/batch и преобразовать ответ в доменные снимки."""
        if not item_ids:
            return {}

        try:
            response = await self._http_client.post(
                self.BATCH_ENDPOINT,
                json={"item_ids": item_ids},
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise CatalogServiceUnavailableError(
                "Сервис каталога временно недоступен"
            ) from exc

        if not isinstance(payload, list):
            raise CatalogServiceUnavailableError(
                "Получен некорректный формат ответа от сервиса каталога"
            )

        snapshots: dict[int, CatalogItemSnapshot] = {}
        for raw_item in payload:
            snapshot = self._parse_snapshot(raw_item)
            snapshots[snapshot.id] = snapshot
        return snapshots

    @staticmethod
    def _parse_snapshot(raw_item: Any) -> CatalogItemSnapshot:
        """Преобразовать JSON-объект BatchItemResponse в CatalogItemSnapshot."""
        if not isinstance(raw_item, dict):
            raise CatalogServiceUnavailableError(
                "Элемент ответа сервиса каталога имеет некорректный формат"
            )
        try:
            return CatalogItemSnapshot(
                id=int(raw_item["id"]),
                title=str(raw_item["title"]),
                author=str(raw_item["author"]),
                price=Decimal(str(raw_item["price"])),
                image_url=raw_item.get("image_url"),
                status=str(raw_item["status"]),
                stock=int(raw_item["stock"]),
                available=bool(raw_item["available"]),
            )
        except (KeyError, TypeError, ValueError, InvalidOperation) as exc:
            raise CatalogServiceUnavailableError(
                "Ответ сервиса каталога не соответствует контракту BatchItemResponse"
            ) from exc
