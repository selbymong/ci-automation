"""Add priority_score table

Revision ID: 006
Revises: 005
Create Date: 2026-04-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "priority_score",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("charity_id", sa.String(36), sa.ForeignKey("charity.id"), nullable=False),
        sa.Column("views_score", sa.Float(), server_default="0"),
        sa.Column("staleness_score", sa.Float(), server_default="0"),
        sa.Column("demand_score", sa.Float(), server_default="0"),
        sa.Column("top100_bonus", sa.Float(), server_default="0"),
        sa.Column("composite_score", sa.Float(), server_default="0"),
        sa.Column("priority_rank", sa.Integer(), server_default="5"),
        sa.Column("page_views", sa.Integer(), nullable=True),
        sa.Column("years_since_eval", sa.Float(), nullable=True),
        sa.Column("demand_votes", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_priority_score_charity_id", "priority_score", ["charity_id"], unique=True)
    op.create_index("ix_priority_score_rank", "priority_score", ["priority_rank", "composite_score"])


def downgrade() -> None:
    op.drop_index("ix_priority_score_rank")
    op.drop_index("ix_priority_score_charity_id")
    op.drop_table("priority_score")
