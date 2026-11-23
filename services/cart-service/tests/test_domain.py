"""Модульные тесты доменного слоя (без фреймворков и БД)."""

from decimal import Decimal

from app.domain.models import Cart, CartItem, CatalogItemSnapshot, UnavailableReason


def _make_snapshot(
    *,
    item_id: int = 1,
    price: str = "500.00",
    status: str = "APPROVED",
    stock: int = 10,
    available: bool = True,
) -> CatalogItemSnapshot:
    return CatalogItemSnapshot(
        id=item_id,
        title="Дюна",
        author="Фрэнк Герберт",
        price=Decimal(price),
        image_url="https://example.com/dune.jpg",
        status=status,
        stock=stock,
        available=available,
    )


def test_cart_item_available_calculates_line_total() -> None:
    snapshot = _make_snapshot(item_id=10, price="890.10", stock=5)
    item = CartItem.from_catalog_snapshot(item_id=10, quantity=3, snapshot=snapshot)

    assert item.available is True
    assert item.unavailable_reason is None
    assert item.message is None
    assert item.line_total == Decimal("2670.30")


def test_cart_item_deleted_marks_unavailable() -> None:
    item = CartItem.from_catalog_snapshot(item_id=99, quantity=2, snapshot=None)

    assert item.available is False
    assert item.unavailable_reason == UnavailableReason.DELETED
    assert item.message == "Товар недоступен"
    assert item.title is None
    assert item.price is None
    assert item.line_total == Decimal("0.00")


def test_cart_item_not_approved_marks_unavailable() -> None:
    snapshot = _make_snapshot(item_id=2, status="BLOCKED", stock=5, available=False)
    item = CartItem.from_catalog_snapshot(item_id=2, quantity=1, snapshot=snapshot)

    assert item.available is False
    assert item.unavailable_reason == UnavailableReason.NOT_APPROVED
    assert item.message == "Товар недоступен"
    assert item.title == "Дюна"
    assert item.line_total == Decimal("0.00")


def test_cart_item_out_of_stock_marks_unavailable() -> None:
    snapshot = _make_snapshot(item_id=3, stock=0, available=False)
    item = CartItem.from_catalog_snapshot(item_id=3, quantity=1, snapshot=snapshot)

    assert item.available is False
    assert item.unavailable_reason == UnavailableReason.OUT_OF_STOCK
    assert item.message == "Товара нет в наличии"
    assert item.line_total == Decimal("0.00")


def test_cart_item_insufficient_stock_marks_unavailable() -> None:
    snapshot = _make_snapshot(item_id=4, stock=2, available=True)
    item = CartItem.from_catalog_snapshot(item_id=4, quantity=5, snapshot=snapshot)

    assert item.available is False
    assert item.unavailable_reason == UnavailableReason.INSUFFICIENT_STOCK
    assert "2" in (item.message or "")
    assert item.line_total == Decimal("0.00")


def test_cart_total_price_excludes_unavailable_items() -> None:
    snapshots = {
        1: _make_snapshot(item_id=1, price="1000.00", stock=5),
        2: _make_snapshot(item_id=2, price="500.00", stock=0, available=False),
    }
    cart = Cart.build(
        user_id="user-1",
        raw_items={1: 2, 2: 1, 3: 1},
        catalog_snapshots=snapshots,
    )

    assert len(cart.items) == 3
    assert cart.total_price == Decimal("2000.00")
    assert cart.has_unavailable_items is True
