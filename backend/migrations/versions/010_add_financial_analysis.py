"""Add financial_analysis table

Revision ID: 010
Revises: 009
Create Date: 2026-04-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '010'
down_revision: Union[str, None] = '009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('financial_analysis',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('charity_id', sa.String(length=36), nullable=False),
        sa.Column('cycle_id', sa.String(length=36), nullable=True),
        sa.Column('fiscal_year_end', sa.String(length=10), nullable=False),
        sa.Column('donations', sa.Float(), nullable=True),
        sa.Column('government_funding', sa.Float(), nullable=True),
        sa.Column('other_revenue', sa.Float(), nullable=True),
        sa.Column('total_revenue', sa.Float(), nullable=True),
        sa.Column('program_costs', sa.Float(), nullable=True),
        sa.Column('admin_costs', sa.Float(), nullable=True),
        sa.Column('fundraising_costs', sa.Float(), nullable=True),
        sa.Column('total_expenses', sa.Float(), nullable=True),
        sa.Column('total_assets', sa.Float(), nullable=True),
        sa.Column('total_liabilities', sa.Float(), nullable=True),
        sa.Column('net_assets', sa.Float(), nullable=True),
        sa.Column('reserves', sa.Float(), nullable=True),
        sa.Column('admin_percent', sa.Float(), nullable=True),
        sa.Column('fundraising_percent', sa.Float(), nullable=True),
        sa.Column('overhead_percent', sa.Float(), nullable=True),
        sa.Column('program_cost_coverage', sa.Float(), nullable=True),
        sa.Column('year_number', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('analyst_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['charity_id'], ['charity.id']),
        sa.ForeignKeyConstraint(['cycle_id'], ['evaluation_cycle.id']),
        sa.ForeignKeyConstraint(['analyst_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('financial_analysis')
