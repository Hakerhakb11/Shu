"""SQLAlchemy database models for Catalog Service."""

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class CategoryModel(Base):
    """Database model for book categories."""

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)

    items = relationship("ItemModel", back_populates="category")


class ItemModel(Base):
    """Database model for catalog book items."""

    __tablename__ = "items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    author = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    price = Column(Float, nullable=False, index=True)
    category_id = Column(
        Integer, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    seller_id = Column(String(100), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="PENDING", index=True)
    image_url = Column(String(1024), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    category = relationship("CategoryModel", back_populates="items", lazy="joined")
    characteristics = relationship(
        "ItemCharacteristicModel",
        back_populates="item",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    stock = relationship(
        "ItemStockModel",
        back_populates="item",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="joined",
    )

    __table_args__ = (
        Index("ix_items_category_status", "category_id", "status"),
        Index("ix_items_price_status", "price", "status"),
    )


class ItemCharacteristicModel(Base):
    """Database model for key-value book characteristics (e.g. ISBN, publisher, condition)."""

    __tablename__ = "item_characteristics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(
        Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = Column(String(100), nullable=False)
    value = Column(String(255), nullable=False)

    item = relationship("ItemModel", back_populates="characteristics")


class ItemStockModel(Base):
    """Database model for item warehouse stock."""

    __tablename__ = "item_stocks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(
        Integer, ForeignKey("items.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    quantity = Column(Integer, nullable=False, default=1)

    item = relationship("ItemModel", back_populates="stock")
