"""Tests for Domain layer logic."""

import pytest

from app.domain.models import (
    Category,
    Item,
    ItemCharacteristic,
    ItemStatus,
    UserRole,
)


def test_item_creation_and_defaults() -> None:
    item = Item(
        title="Война и мир",
        author="Лев Толстой",
        description="Классическое произведение",
        price=550.0,
        category_id=1,
        seller_id="seller_123",
    )
    assert item.status == ItemStatus.PENDING
    assert item.stock == 1
    assert item.is_available() is False  # PENDING items are not available for buying


def test_item_status_transitions() -> None:
    item = Item(
        title="Мастер и Маргарита",
        author="Михаил Булгаков",
        description="Роман",
        price=450.0,
        category_id=1,
        seller_id="seller_123",
    )
    assert item.status == ItemStatus.PENDING

    item.approve()
    assert item.status == ItemStatus.APPROVED
    assert item.is_available() is True

    item.update_stock(0)
    assert item.is_available() is False

    item.reject()
    assert item.status == ItemStatus.REJECTED

    item.block()
    assert item.status == ItemStatus.BLOCKED


def test_item_stock_negative_raises() -> None:
    item = Item(
        title="Тест",
        author="Автор",
        description="Описание",
        price=100.0,
        category_id=1,
        seller_id="s1",
    )
    with pytest.raises(ValueError):
        item.update_stock(-5)


def test_item_permissions_edit_and_delete() -> None:
    item = Item(
        title="Преступление и наказание",
        author="Федор Достоевский",
        description="Роман",
        price=350.0,
        category_id=1,
        seller_id="seller_100",
    )

    # Owner seller can edit/delete
    assert item.can_be_edited_by("seller_100", UserRole.SELLER) is True
    assert item.can_be_deleted_by("seller_100", UserRole.SELLER) is True

    # Other seller CANNOT edit/delete
    assert item.can_be_edited_by("seller_999", UserRole.SELLER) is False
    assert item.can_be_deleted_by("seller_999", UserRole.SELLER) is False

    # Moderator can edit/delete ANY item
    assert item.can_be_edited_by("mod_1", UserRole.MODERATOR) is True
    assert item.can_be_deleted_by("mod_1", UserRole.MODERATOR) is True

    # Client cannot edit/delete
    assert item.can_be_edited_by("client_1", UserRole.CLIENT) is False
    assert item.can_be_deleted_by("client_1", UserRole.CLIENT) is False


def test_category_and_characteristics() -> None:
    cat = Category(id=1, name="Художественная литература", slug="fiction")
    char = ItemCharacteristic(name="ISBN", value="978-5-17-090876-5")
    assert cat.name == "Художественная литература"
    assert char.name == "ISBN"
