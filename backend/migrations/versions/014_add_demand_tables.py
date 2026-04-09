"""Add charity_request and demand_aggregate tables

Revision ID: 014
Revises: 013
Create Date: 2026-04-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '014'
down_revision: Union[str, None] = '013'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('charity_request',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('requester_name', sa.String(length=200), nullable=False),
        sa.Column('requester_email', sa.String(length=255), nullable=False),
        sa.Column('requested_charity_name', sa.String(length=300), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('matched_charity_id', sa.String(length=36), nullable=True),
        sa.Column('disposition', sa.String(length=30), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['matched_charity_id'], ['charity.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('demand_aggregate',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('charity_id', sa.String(length=36), nullable=False),
        sa.Column('vote_count', sa.Integer(), nullable=False),
        sa.Column('disposition', sa.String(length=30), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['charity_id'], ['charity.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('charity_id')
    )


def downgrade() -> None:
    op.drop_table('demand_aggregate')
    op.drop_table('charity_request')
