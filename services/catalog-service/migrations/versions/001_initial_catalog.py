"""Initial catalog schema with full-text search and GIN indexes

Revision ID: 001_initial_catalog
Revises:
Create Date: 2026-11-22 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial_catalog"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # Optional: Enable pg_trgm extension on Postgres for trigram fuzzy search
    if is_postgres:
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    # 1. Categories
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_categories_name"), "categories", ["name"], unique=False)
    op.create_index(op.f("ix_categories_slug"), "categories", ["slug"], unique=False)

    # 2. Items
    op.create_table(
        "items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("author", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("seller_id", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("image_url", sa.String(length=1024), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_items_title"), "items", ["title"], unique=False)
    op.create_index(op.f("ix_items_author"), "items", ["author"], unique=False)
    op.create_index(op.f("ix_items_price"), "items", ["price"], unique=False)
    op.create_index(op.f("ix_items_category_id"), "items", ["category_id"], unique=False)
    op.create_index(op.f("ix_items_seller_id"), "items", ["seller_id"], unique=False)
    op.create_index(op.f("ix_items_status"), "items", ["status"], unique=False)
    op.create_index("ix_items_category_status", "items", ["category_id", "status"], unique=False)
    op.create_index("ix_items_price_status", "items", ["price", "status"], unique=False)

    # GIN Full-Text Search and Trigram index on Postgres
    if is_postgres:
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_items_fts_gin
            ON items
            USING gin(to_tsvector(
                'russian',
                coalesce(title, '') || ' ' || coalesce(author, '')
                || ' ' || coalesce(description, '')
            ));
            """
        )
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_items_title_trgm
            ON items
            USING gin(title gin_trgm_ops);
            """
        )

    # 3. Item Characteristics
    op.create_table(
        "item_characteristics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("value", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_item_characteristics_item_id"), "item_characteristics", ["item_id"], unique=False
    )

    # 4. Item Stocks
    op.create_table(
        "item_stocks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("item_id"),
    )
    op.create_index(op.f("ix_item_stocks_item_id"), "item_stocks", ["item_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    if is_postgres:
        op.execute("DROP INDEX IF EXISTS idx_items_title_trgm;")
        op.execute("DROP INDEX IF EXISTS idx_items_fts_gin;")

    op.drop_table("item_stocks")
    op.drop_table("item_characteristics")
    op.drop_table("items")
    op.drop_table("categories")
