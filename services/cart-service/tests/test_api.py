"""Интеграционные тесты HTTP API и клиентов инфраструктуры."""

from decimal import Decimal

import httpx
import pytest

from app.domain.exceptions import CatalogServiceUnavailableError
from app.domain.models import CatalogItemSnapshot
from app.infrastructure.clients.catalog_client import HttpCatalogClient
from tests.conftest import FakeCatalogClient, InMemoryCartRepository


@pytest.mark.asyncio
async def test_missing_user_id_header_returns_401(api_client: httpx.AsyncClient) -> None:
    response = await api_client.get("/cart")
    assert response.status_code == 401
    body = response.json()
    assert body["error_code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_full_cart_lifecycle(
    api_client: httpx.AsyncClient,
    fake_catalog: FakeCatalogClient,
) -> None:
    headers = {"X-User-Id": "user-42"}
    fake_catalog.snapshots[42] = CatalogItemSnapshot(
        id=42,
        title="Автостопом по галактике",
        author="Дуглас Адамс",
        price=Decimal("650.00"),
        image_url="https://example.com/h2g2.jpg",
        status="APPROVED",
        stock=10,
        available=True,
    )

    # 1. Add items
    resp_add = await api_client.post(
        "/cart/items",
        headers=headers,
        json={"item_id": 42, "quantity": 2},
    )
    assert resp_add.status_code == 200
    assert resp_add.json() == {"item_id": 42, "quantity": 2}

    # Add a deleted item
    await api_client.post("/cart/items", headers=headers, json={"item_id": 777, "quantity": 1})

    # 2. Get cart
    resp_get = await api_client.get("/cart", headers=headers)
    assert resp_get.status_code == 200
    data = resp_get.json()
    assert data["user_id"] == "user-42"
    assert data["total_price"] == 1300.0
    assert data["has_unavailable_items"] is True
    assert len(data["items"]) == 2
    assert data["items"][0]["available"] is True
    assert data["items"][1]["available"] is False
    assert data["items"][1]["unavailable_reason"] == "DELETED"
    assert data["items"][1]["message"] == "Товар недоступен"

    # 3. Decrement item
    resp_dec = await api_client.delete("/cart/items/42?quantity=1", headers=headers)
    assert resp_dec.status_code == 200
    assert resp_dec.json() == {"item_id": 42, "quantity": 1}

    # 4. Delete missing item -> 404
    resp_404 = await api_client.delete("/cart/items/9999", headers=headers)
    assert resp_404.status_code == 404
    assert resp_404.json()["error_code"] == "ITEM_NOT_IN_CART"

    # 5. Clear cart -> 204
    resp_clear = await api_client.delete("/cart", headers=headers)
    assert resp_clear.status_code == 204

    resp_empty = await api_client.get("/cart", headers=headers)
    assert resp_empty.status_code == 200
    assert resp_empty.json()["items"] == []
    assert resp_empty.json()["total_price"] == 0.0


@pytest.mark.asyncio
async def test_catalog_unavailable_returns_503(
    api_client: httpx.AsyncClient,
    fake_catalog: FakeCatalogClient,
) -> None:
    headers = {"X-User-Id": "user-503"}
    await api_client.post("/cart/items", headers=headers, json={"item_id": 1, "quantity": 1})
    fake_catalog.should_fail = True

    response = await api_client.get("/cart", headers=headers)
    assert response.status_code == 503
    assert response.json()["error_code"] == "CATALOG_SERVICE_UNAVAILABLE"


@pytest.mark.asyncio
async def test_health_endpoint(
    api_client: httpx.AsyncClient,
    fake_repo: InMemoryCartRepository,
) -> None:
    ok_resp = await api_client.get("/health")
    assert ok_resp.status_code == 200
    assert ok_resp.json() == {"status": "ok", "redis": "ok"}

    fake_repo.is_healthy = False
    down_resp = await api_client.get("/health")
    assert down_resp.status_code == 503
    assert down_resp.json()["error_code"] == "CART_STORAGE_UNAVAILABLE"


@pytest.mark.asyncio
async def test_http_catalog_client_parses_batch_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/catalog/items/batch"
        return httpx.Response(
            200,
            json=[
                {
                    "id": 10,
                    "title": "1984",
                    "author": "Джордж Оруэлл",
                    "price": 550.5,
                    "image_url": None,
                    "status": "APPROVED",
                    "stock": 3,
                    "available": True,
                }
            ],
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://catalog") as client:
        catalog_client = HttpCatalogClient(client)
        result = await catalog_client.get_items_batch([10, 20])

    assert 10 in result
    assert 20 not in result
    assert result[10].price == Decimal("550.5")
    assert result[10].title == "1984"


@pytest.mark.asyncio
async def test_http_catalog_client_raises_on_500() -> None:
    transport = httpx.MockTransport(lambda _req: httpx.Response(500))
    async with httpx.AsyncClient(transport=transport, base_url="http://catalog") as client:
        catalog_client = HttpCatalogClient(client)
        with pytest.raises(CatalogServiceUnavailableError):
            await catalog_client.get_items_batch([10])
