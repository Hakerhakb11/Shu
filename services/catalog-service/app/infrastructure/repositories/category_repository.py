"""Category repository implementation using SQLAlchemy."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces import CategoryRepositoryInterface
from app.domain.models import Category
from app.infrastructure.db.models import CategoryModel


class CategoryRepository(CategoryRepositoryInterface):
    """SQLAlchemy repository for categories."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _to_domain(model: CategoryModel) -> Category:
        return Category(
            id=model.id,
            name=model.name,
            slug=model.slug,
            description=model.description,
        )

    async def get_all(self) -> list[Category]:
        stmt = select(CategoryModel).order_by(CategoryModel.name)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def get_by_id(self, category_id: int) -> Category | None:
        stmt = select(CategoryModel).where(CategoryModel.id == category_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_slug(self, slug: str) -> Category | None:
        stmt = select(CategoryModel).where(CategoryModel.slug == slug)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def create(self, category: Category) -> Category:
        model = CategoryModel(
            name=category.name,
            slug=category.slug,
            description=category.description,
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_domain(model)
