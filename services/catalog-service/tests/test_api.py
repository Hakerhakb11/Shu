"""End-to-end API tests for Catalog Service endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "catalog-service"}


@pytest.mark.asyncio
async def test_categories_crud(client: AsyncClient) -> None:
    # 1. Create Category
    resp = await client.post(
        "/catalog/categories",
        json={"name": "Научная фантастика", "slug": "sci-fi", "description": "Книги жанра sci-fi"},
    )
    assert resp.status_code == 201
    cat_data = resp.json()
    assert cat_data["id"] is not None
    assert cat_data["slug"] == "sci-fi"

    # 2. List Categories
    list_resp = await client.get("/catalog/categories")
    assert list_resp.status_code == 200
    categories = list_resp.json()
    assert len(categories) >= 1
    assert any(c["slug"] == "sci-fi" for c in categories)


@pytest.mark.asyncio
async def test_seller_item_creation_and_role_protection(client: AsyncClient) -> None:
    # Create category first
    cat_resp = await client.post(
        "/catalog/categories",
        json={"name": "Детективы", "slug": "detective", "description": "Детективные романы"},
    )
    category_id = cat_resp.json()["id"]

    item_payload = {
        "title": "Убийство в Восточном экспрессе",
        "author": "Агата Кристи",
        "description": "Классический детектив Эркюля Пуаро в отличном состоянии",
        "price": 350.0,
        "category_id": category_id,
        "stock": 1,
        "image_url": "https://example.com/agatha.jpg",
        "characteristics": [
            {"name": "Издательство", "value": "Эксмо"},
            {"name": "Год издания", "value": "2020"},
            {"name": "Состояние", "value": "Отличное"},
        ],
    }

    # 1. Forbidden for CLIENT role
    client_resp = await client.post(
        "/catalog/items",
        json=item_payload,
        headers={"X-User-Role": "CLIENT", "X-User-Id": "123"},
    )
    assert client_resp.status_code == 403

    # 2. Forbidden if no role header
    no_role_resp = await client.post("/catalog/items", json=item_payload)
    assert no_role_resp.status_code == 403

    # 3. Successful for SELLER role -> status PENDING
    seller_resp = await client.post(
        "/catalog/items",
        json=item_payload,
        headers={"X-User-Role": "SELLER", "X-User-Id": "seller_42"},
    )
    assert seller_resp.status_code == 201
    item = seller_resp.json()
    assert item["id"] is not None
    assert item["status"] == "PENDING"
    assert item["seller_id"] == "seller_42"
    assert len(item["characteristics"]) == 3


@pytest.mark.asyncio
async def test_moderator_workflow_and_public_visibility(client: AsyncClient) -> None:
    # 1. Create Category
    cat_resp = await client.post(
        "/catalog/categories",
        json={"name": "Классика", "slug": "classic", "description": "Классическая литература"},
    )
    category_id = cat_resp.json()["id"]

    # 2. Seller creates item
    seller_resp = await client.post(
        "/catalog/items",
        json={
            "title": "Идиот",
            "author": "Федор Достоевский",
            "description": "Роман",
            "price": 400.0,
            "category_id": category_id,
            "stock": 1,
        },
        headers={"X-User-Role": "SELLER", "X-User-Id": "seller_1"},
    )
    item_id = seller_resp.json()["id"]

    # 3. Public listing must NOT show PENDING items
    pub_resp = await client.get("/catalog/items")
    assert pub_resp.status_code == 200
    items = pub_resp.json()["items"]
    assert all(i["id"] != item_id for i in items)

    # 4. Moderator listing: CLIENT or SELLER cannot view moderation queue
    mod_client_resp = await client.get(
        "/catalog/moderation/items",
        headers={"X-User-Role": "CLIENT", "X-User-Id": "client_1"},
    )
    assert mod_client_resp.status_code == 403

    mod_seller_resp = await client.get(
        "/catalog/moderation/items",
        headers={"X-User-Role": "SELLER", "X-User-Id": "seller_1"},
    )
    assert mod_seller_resp.status_code == 403

    # 5. Moderator can view moderation queue
    mod_resp = await client.get(
        "/catalog/moderation/items",
        headers={"X-User-Role": "MODERATOR", "X-User-Id": "mod_1"},
    )
    assert mod_resp.status_code == 200
    mod_items = mod_resp.json()["items"]
    assert any(i["id"] == item_id for i in mod_items)

    # 6. Moderator approves item
    patch_resp = await client.patch(
        f"/catalog/items/{item_id}/status",
        json={"status": "APPROVED"},
        headers={"X-User-Role": "MODERATOR", "X-User-Id": "mod_1"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "APPROVED"

    # 7. Now public catalog shows the item!
    pub_resp_after = await client.get("/catalog/items")
    assert pub_resp_after.status_code == 200
    after_items = pub_resp_after.json()["items"]
    assert any(i["id"] == item_id for i in after_items)

    # 8. Single item detail (cached)
    detail_resp = await client.get(f"/catalog/items/{item_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == item_id
    assert detail_resp.json()["title"] == "Идиот"


@pytest.mark.asyncio
async def test_search_and_filters(client: AsyncClient) -> None:
    cat1_resp = await client.post("/catalog/categories", json={"name": "Поэзия", "slug": "poetry"})
    cat1_id = cat1_resp.json()["id"]

    # Create and approve book 1
    item1 = (
        await client.post(
            "/catalog/items",
            json={
                "title": "Евгений Онегин",
                "author": "Александр Пушкин",
                "description": "Роман в стихах",
                "price": 200.0,
                "category_id": cat1_id,
            },
            headers={"X-User-Role": "SELLER", "X-User-Id": "seller_1"},
        )
    ).json()

    # Create and approve book 2
    item2 = (
        await client.post(
            "/catalog/items",
            json={
                "title": "Стихотворения",
                "author": "Михаил Лермонтов",
                "description": "Сборник лирики",
                "price": 600.0,
                "category_id": cat1_id,
            },
            headers={"X-User-Role": "SELLER", "X-User-Id": "seller_1"},
        )
    ).json()

    # Approve both
    for it in [item1, item2]:
        await client.patch(
            f"/catalog/items/{it['id']}/status",
            json={"status": "APPROVED"},
            headers={"X-User-Role": "MODERATOR", "X-User-Id": "mod_1"},
        )

    # Filter by price: min_price=300
    res_price = await client.get("/catalog/items", params={"min_price": 300})
    assert res_price.status_code == 200
    items = res_price.json()["items"]
    assert any(i["id"] == item2["id"] for i in items)
    assert all(i["id"] != item1["id"] for i in items)

    # Search by author "Пушкин"
    res_search = await client.get("/catalog/items", params={"search": "Пушкин"})
    assert res_search.status_code == 200
    search_items = res_search.json()["items"]
    assert any(i["id"] == item1["id"] for i in search_items)
    assert all(i["id"] != item2["id"] for i in search_items)


@pytest.mark.asyncio
async def test_update_and_delete_permissions(client: AsyncClient) -> None:
    cat_resp = await client.post(
        "/catalog/categories", json={"name": "Детские книги", "slug": "kids"}
    )
    category_id = cat_resp.json()["id"]

    create_resp = await client.post(
        "/catalog/items",
        json={
            "title": "Сказки",
            "author": "Корней Чуковский",
            "description": "Сказки для детей",
            "price": 250.0,
            "category_id": category_id,
        },
        headers={"X-User-Role": "SELLER", "X-User-Id": "seller_owner"},
    )
    item_id = create_resp.json()["id"]

    # 1. Other seller attempts PUT -> 403
    other_put = await client.put(
        f"/catalog/items/{item_id}",
        json={"title": "Взломанное название"},
        headers={"X-User-Role": "SELLER", "X-User-Id": "seller_other"},
    )
    assert other_put.status_code == 403

    # 2. Client attempts PUT -> 403
    client_put = await client.put(
        f"/catalog/items/{item_id}",
        json={"title": "Взломанное название"},
        headers={"X-User-Role": "CLIENT", "X-User-Id": "client_1"},
    )
    assert client_put.status_code == 403

    # 3. Owner seller successfully updates
    owner_put = await client.put(
        f"/catalog/items/{item_id}",
        json={"title": "Сказки для малышей", "price": 270.0},
        headers={"X-User-Role": "SELLER", "X-User-Id": "seller_owner"},
    )
    assert owner_put.status_code == 200
    assert owner_put.json()["title"] == "Сказки для малышей"
    assert owner_put.json()["price"] == 270.0

    # 4. Moderator can update ANY item
    mod_put = await client.put(
        f"/catalog/items/{item_id}",
        json={"description": "Проверено модератором"},
        headers={"X-User-Role": "MODERATOR", "X-User-Id": "mod_1"},
    )
    assert mod_put.status_code == 200
    assert mod_put.json()["description"] == "Проверено модератором"

    # 5. Other seller attempts DELETE -> 403
    other_del = await client.delete(
        f"/catalog/items/{item_id}",
        headers={"X-User-Role": "SELLER", "X-User-Id": "seller_other"},
    )
    assert other_del.status_code == 403

    # 6. Owner seller successfully deletes
    owner_del = await client.delete(
        f"/catalog/items/{item_id}",
        headers={"X-User-Role": "SELLER", "X-User-Id": "seller_owner"},
    )
    assert owner_del.status_code == 204

    # 7. GET item now returns 404
    get_del = await client.get(f"/catalog/items/{item_id}")
    assert get_del.status_code == 404


@pytest.mark.asyncio
async def test_batch_items_endpoint_for_cart_service(client: AsyncClient) -> None:
    cat_resp = await client.post(
        "/catalog/categories", json={"name": "Энциклопедии", "slug": "encyclopedia"}
    )
    category_id = cat_resp.json()["id"]

    # Item 1: Approved
    item1 = (
        await client.post(
            "/catalog/items",
            json={
                "title": "Большая энциклопедия",
                "author": "Коллектив авторов",
                "description": "Том 1",
                "price": 1500.0,
                "category_id": category_id,
                "stock": 2,
            },
            headers={"X-User-Role": "SELLER", "X-User-Id": "seller_1"},
        )
    ).json()

    await client.patch(
        f"/catalog/items/{item1['id']}/status",
        json={"status": "APPROVED"},
        headers={"X-User-Role": "MODERATOR", "X-User-Id": "mod_1"},
    )

    # Item 2: Pending (not approved yet)
    item2 = (
        await client.post(
            "/catalog/items",
            json={
                "title": "Малая энциклопедия",
                "author": "Коллектив авторов",
                "description": "Том 2",
                "price": 800.0,
                "category_id": category_id,
                "stock": 1,
            },
            headers={"X-User-Role": "SELLER", "X-User-Id": "seller_1"},
        )
    ).json()

    # Batch request for [item1['id'], item2['id'], 99999]
    batch_resp = await client.post(
        "/catalog/items/batch",
        json={"item_ids": [item1["id"], item2["id"], 99999]},
    )
    assert batch_resp.status_code == 200
    batch_items = batch_resp.json()
    assert len(batch_items) == 2

    item1_info = next(i for i in batch_items if i["id"] == item1["id"])
    assert item1_info["available"] is True
    assert item1_info["price"] == 1500.0

    item2_info = next(i for i in batch_items if i["id"] == item2["id"])
    assert item2_info["available"] is False  # PENDING status is not available for purchase!
