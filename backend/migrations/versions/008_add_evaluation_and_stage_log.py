"""Add evaluation and evaluation_stage_log tables

Revision ID: 008
Revises: 007
Create Date: 2026-04-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "evaluation",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("charity_id", sa.String(36), sa.ForeignKey("charity.id"), nullable=False),
        sa.Column("cycle_id", sa.String(36), sa.ForeignKey("evaluation_cycle.id"), nullable=False),
        sa.Column("stage", sa.String(30), nullable=False, server_default="prioritized"),
        sa.Column("analyst_id", sa.String(36), sa.ForeignKey("user.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_evaluation_cycle", "evaluation", ["cycle_id"])
    op.create_index("ix_evaluation_charity_cycle", "evaluation", ["charity_id", "cycle_id"], unique=True)
    op.create_index("ix_evaluation_stage", "evaluation", ["stage"])

    op.create_table(
        "evaluation_stage_log",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("evaluation_id", sa.String(36), sa.ForeignKey("evaluation.id"), nullable=False),
        sa.Column("from_stage", sa.String(30), nullable=False),
        sa.Column("to_stage", sa.String(30), nullable=False),
        sa.Column("actor_id", sa.String(36), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("transitioned_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_stage_log_evaluation", "evaluation_stage_log", ["evaluation_id"])


def downgrade() -> None:
    op.drop_index("ix_stage_log_evaluation")
    op.drop_table("evaluation_stage_log")
    op.drop_index("ix_evaluation_stage")
    op.drop_index("ix_evaluation_charity_cycle")
    op.drop_index("ix_evaluation_cycle")
    op.drop_table("evaluation")
