"""Add sector, sub_sector, sector_group tables

Revision ID: 003
Revises: 002
Create Date: 2026-04-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sector_group",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), unique=True, nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "sector",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), unique=True, nullable=False),
        sa.Column("group_id", sa.String(36), sa.ForeignKey("sector_group.id"), nullable=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "sub_sector",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("sector_id", sa.String(36), sa.ForeignKey("sector.id"), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("sub_sector")
    op.drop_table("sector")
    op.drop_table("sector_group")
