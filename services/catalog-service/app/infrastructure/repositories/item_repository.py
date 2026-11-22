"""Item repository implementation using SQLAlchemy."""

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.application.interfaces import ItemRepositoryInterface
from app.domain.models import Category, Item, ItemCharacteristic, ItemStatus
from app.infrastructure.db.models import (
    ItemCharacteristicModel,
    ItemModel,
    ItemStockModel,
)


class ItemRepository(ItemRepositoryInterface):
    """SQLAlchemy repository for marketplace book items."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _to_domain(model: ItemModel) -> Item:
        characteristics = [
            ItemCharacteristic(
                id=c.id,
                name=c.name,
                value=c.value,
                item_id=c.item_id,
            )
            for c in (model.characteristics or [])
        ]
        category = None
        if model.category:
            category = Category(
                id=model.category.id,
                name=model.category.name,
                slug=model.category.slug,
                description=model.category.description,
            )

        stock_quantity = model.stock.quantity if model.stock is not None else 0

        return Item(
            id=model.id,
            title=model.title,
            author=model.author,
            description=model.description,
            price=model.price,
            category_id=model.category_id,
            seller_id=str(model.seller_id),
            status=ItemStatus(model.status),
            image_url=model.image_url,
            stock=stock_quantity,
            characteristics=characteristics,
            category=category,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_by_id(self, item_id: int) -> Item | None:
        stmt = (
            select(ItemModel)
            .where(ItemModel.id == item_id)
            .options(
                selectinload(ItemModel.characteristics),
                selectinload(ItemModel.category),
                selectinload(ItemModel.stock),
            )
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_batch(self, item_ids: list[int]) -> list[Item]:
        if not item_ids:
            return []
        stmt = (
            select(ItemModel)
            .where(ItemModel.id.in_(item_ids))
            .options(
                selectinload(ItemModel.characteristics),
                selectinload(ItemModel.category),
                selectinload(ItemModel.stock),
            )
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def list_items(
        self,
        page: int,
        size: int,
        category_id: int | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        search: str | None = None,
        status: ItemStatus | None = None,
    ) -> tuple[list[Item], int]:
        stmt = select(ItemModel).options(
            selectinload(ItemModel.characteristics),
            selectinload(ItemModel.category),
            selectinload(ItemModel.stock),
        )

        if category_id is not None:
            stmt = stmt.where(ItemModel.category_id == category_id)

        if min_price is not None:
            stmt = stmt.where(ItemModel.price >= min_price)

        if max_price is not None:
            stmt = stmt.where(ItemModel.price <= max_price)

        if status is not None:
            stmt = stmt.where(ItemModel.status == status.value)

        if search and search.strip():
            clean_search = search.strip()
            # Check dialect
            dialect_name = self.session.bind.dialect.name if self.session.bind else ""
            if dialect_name == "postgresql":
                # Full-Text Search via tsvector (russian) + ILIKE fallback
                ts_vector = func.to_tsvector(
                    "russian",
                    func.concat(
                        ItemModel.title,
                        " ",
                        func.coalesce(ItemModel.author, ""),
                        " ",
                        func.coalesce(ItemModel.description, ""),
                    ),
                )
                ts_query = func.plainto_tsquery("russian", clean_search)
                stmt = stmt.where(
                    or_(
                        ts_vector.op("@@")(ts_query),
                        ItemModel.title.ilike(f"%{clean_search}%"),
                        ItemModel.author.ilike(f"%{clean_search}%"),
                    )
                )
            else:
                # Portable fallback (SQLite / tests)
                stmt = stmt.where(
                    or_(
                        ItemModel.title.ilike(f"%{clean_search}%"),
                        ItemModel.author.ilike(f"%{clean_search}%"),
                        ItemModel.description.ilike(f"%{clean_search}%"),
                    )
                )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
        total_res = await self.session.execute(count_stmt)
        total = total_res.scalar_one()

        # Pagination & sorting
        offset = (page - 1) * size
        stmt = stmt.order_by(ItemModel.id.desc()).offset(offset).limit(size)

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models], total

    async def create(self, item: Item) -> Item:
        model = ItemModel(
            title=item.title,
            author=item.author,
            description=item.description,
            price=item.price,
            category_id=item.category_id,
            seller_id=str(item.seller_id),
            status=item.status.value,
            image_url=item.image_url,
        )
        self.session.add(model)
        await self.session.flush()

        stock_model = ItemStockModel(
            item_id=model.id,
            quantity=item.stock,
        )
        self.session.add(stock_model)

        for char in item.characteristics:
            char_model = ItemCharacteristicModel(
                item_id=model.id,
                name=char.name,
                value=char.value,
            )
            self.session.add(char_model)

        await self.session.flush()
        return await self.get_by_id(model.id)  # type: ignore[return-value]

    async def update(self, item: Item) -> Item:
        stmt = (
            select(ItemModel)
            .where(ItemModel.id == item.id)
            .options(
                selectinload(ItemModel.characteristics),
                selectinload(ItemModel.stock),
            )
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one()

        model.title = item.title
        model.author = item.author
        model.description = item.description
        model.price = item.price
        model.category_id = item.category_id
        model.image_url = item.image_url

        if model.stock:
            model.stock.quantity = item.stock
        else:
            self.session.add(ItemStockModel(item_id=model.id, quantity=item.stock))

        # Re-sync characteristics
        model.characteristics.clear()
        for char in item.characteristics:
            model.characteristics.append(
                ItemCharacteristicModel(
                    item_id=model.id,
                    name=char.name,
                    value=char.value,
                )
            )

        await self.session.flush()
        return await self.get_by_id(model.id)  # type: ignore[return-value]

    async def delete(self, item_id: int) -> bool:
        stmt = select(ItemModel).where(ItemModel.id == item_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            await self.session.flush()
            return True
        return False

    async def update_status(self, item_id: int, status: ItemStatus) -> Item:
        stmt = select(ItemModel).where(ItemModel.id == item_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one()
        model.status = status.value
        await self.session.flush()
        return await self.get_by_id(item_id)  # type: ignore[return-value]
