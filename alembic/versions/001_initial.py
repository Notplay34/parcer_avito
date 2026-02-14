"""Initial schema: users, searches, seen_ads.

Revision ID: 001
Revises:
Create Date: 2025-02-14

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=True)

    op.create_table(
        "searches",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("search_url", sa.Text(), nullable=False),
        sa.Column("max_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("last_check_at", sa.DateTime(), nullable=True),
        sa.Column("blocked_until", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "seen_ads",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("search_id", sa.Integer(), nullable=False),
        sa.Column("avito_ad_id", sa.String(64), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["search_id"], ["searches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("search_id", "avito_ad_id", name="uq_search_avito_ad"),
    )
    op.create_index("ix_seen_ads_avito_ad_id", "seen_ads", ["avito_ad_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_seen_ads_avito_ad_id", "seen_ads")
    op.drop_table("seen_ads")
    op.drop_table("searches")
    op.drop_index("ix_users_telegram_id", "users")
    op.drop_table("users")
