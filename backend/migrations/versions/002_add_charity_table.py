"""Add charity table

Revision ID: 002
Revises: 001
Create Date: 2026-04-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "charity",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("cra_number", sa.String(15), unique=True, nullable=False),
        sa.Column("formal_name", sa.String(500), nullable=False),
        sa.Column("common_name", sa.String(500), nullable=True),
        sa.Column("sector", sa.String(100), nullable=True),
        sa.Column("sub_sector", sa.String(100), nullable=True),
        sa.Column("fiscal_year_end", sa.Date(), nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("province", sa.String(50), nullable=True),
        sa.Column("is_top_100", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_charity_cra_number", "charity", ["cra_number"])
    op.create_index("ix_charity_formal_name", "charity", ["formal_name"])


def downgrade() -> None:
    op.drop_index("ix_charity_formal_name")
    op.drop_index("ix_charity_cra_number")
    op.drop_table("charity")
