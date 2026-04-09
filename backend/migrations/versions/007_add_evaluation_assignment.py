"""Add evaluation_assignment table

Revision ID: 007
Revises: 006
Create Date: 2026-04-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "evaluation_assignment",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("analyst_id", sa.String(36), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("charity_id", sa.String(36), sa.ForeignKey("charity.id"), nullable=False),
        sa.Column("cycle_id", sa.String(36), sa.ForeignKey("evaluation_cycle.id"), nullable=False),
        sa.Column("assigned_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("reassigned_from_id", sa.String(36), sa.ForeignKey("user.id"), nullable=True),
        sa.Column("reassignment_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_assignment_cycle", "evaluation_assignment", ["cycle_id"])
    op.create_index("ix_assignment_analyst", "evaluation_assignment", ["analyst_id"])
    op.create_index(
        "ix_assignment_unique_charity_cycle",
        "evaluation_assignment",
        ["charity_id", "cycle_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_assignment_unique_charity_cycle")
    op.drop_index("ix_assignment_analyst")
    op.drop_index("ix_assignment_cycle")
    op.drop_table("evaluation_assignment")
