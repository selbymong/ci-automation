"""Add transparency_config, financial_adjustment, charity_rating tables

Revision ID: 011
Revises: 010
Create Date: 2026-04-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '011'
down_revision: Union[str, None] = '010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('transparency_config',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('charity_id', sa.String(length=36), nullable=False),
        sa.Column('show_donations', sa.Boolean(), nullable=False),
        sa.Column('show_government_funding', sa.Boolean(), nullable=False),
        sa.Column('show_other_revenue', sa.Boolean(), nullable=False),
        sa.Column('show_total_revenue', sa.Boolean(), nullable=False),
        sa.Column('show_program_costs', sa.Boolean(), nullable=False),
        sa.Column('show_admin_costs', sa.Boolean(), nullable=False),
        sa.Column('show_fundraising_costs', sa.Boolean(), nullable=False),
        sa.Column('show_total_expenses', sa.Boolean(), nullable=False),
        sa.Column('show_total_assets', sa.Boolean(), nullable=False),
        sa.Column('show_total_liabilities', sa.Boolean(), nullable=False),
        sa.Column('show_net_assets', sa.Boolean(), nullable=False),
        sa.Column('show_reserves', sa.Boolean(), nullable=False),
        sa.Column('show_admin_percent', sa.Boolean(), nullable=False),
        sa.Column('show_fundraising_percent', sa.Boolean(), nullable=False),
        sa.Column('show_overhead_percent', sa.Boolean(), nullable=False),
        sa.Column('show_program_cost_coverage', sa.Boolean(), nullable=False),
        sa.Column('show_compensation', sa.Boolean(), nullable=False),
        sa.Column('show_endowment', sa.Boolean(), nullable=False),
        sa.Column('show_capital_assets', sa.Boolean(), nullable=False),
        sa.Column('show_pension', sa.Boolean(), nullable=False),
        sa.Column('show_deferred_revenue', sa.Boolean(), nullable=False),
        sa.Column('show_foreign_activity', sa.Boolean(), nullable=False),
        sa.Column('show_gifts_to_other_charities', sa.Boolean(), nullable=False),
        sa.Column('show_political_expenditure', sa.Boolean(), nullable=False),
        sa.Column('show_staff_count', sa.Boolean(), nullable=False),
        sa.Column('show_volunteer_count', sa.Boolean(), nullable=False),
        sa.Column('show_board_compensation', sa.Boolean(), nullable=False),
        sa.Column('show_top10_compensation', sa.Boolean(), nullable=False),
        sa.Column('show_related_party', sa.Boolean(), nullable=False),
        sa.Column('show_professional_fundraiser', sa.Boolean(), nullable=False),
        sa.Column('transparency_score', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['charity_id'], ['charity.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('charity_id')
    )

    op.create_table('financial_adjustment',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('charity_id', sa.String(length=36), nullable=False),
        sa.Column('analysis_id', sa.String(length=36), nullable=True),
        sa.Column('adjustment_type', sa.String(length=30), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=True),
        sa.Column('field_affected', sa.String(length=50), nullable=True),
        sa.Column('analyst_id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['charity_id'], ['charity.id']),
        sa.ForeignKeyConstraint(['analysis_id'], ['financial_analysis.id']),
        sa.ForeignKeyConstraint(['analyst_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('charity_rating',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('charity_id', sa.String(length=36), nullable=False),
        sa.Column('cycle_id', sa.String(length=36), nullable=True),
        sa.Column('star_rating', sa.Integer(), nullable=True),
        sa.Column('impact_x', sa.Float(), nullable=True),
        sa.Column('impact_y', sa.Float(), nullable=True),
        sa.Column('impact_label', sa.String(length=50), nullable=True),
        sa.Column('admin_percent', sa.Float(), nullable=True),
        sa.Column('fundraising_percent', sa.Float(), nullable=True),
        sa.Column('overhead_percent', sa.Float(), nullable=True),
        sa.Column('program_cost_coverage', sa.Float(), nullable=True),
        sa.Column('srss_score', sa.Float(), nullable=True),
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
    op.drop_table('charity_rating')
    op.drop_table('financial_adjustment')
    op.drop_table('transparency_config')
