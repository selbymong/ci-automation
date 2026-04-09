"""Add srss_score, srss_historical, profile_content tables

Revision ID: 012
Revises: 011
Create Date: 2026-04-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '012'
down_revision: Union[str, None] = '011'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('srss_score',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('charity_id', sa.String(length=36), nullable=False),
        sa.Column('cycle_id', sa.String(length=36), nullable=True),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('q1', sa.Integer(), nullable=True),
        sa.Column('q2', sa.Integer(), nullable=True),
        sa.Column('q3', sa.Integer(), nullable=True),
        sa.Column('q4', sa.Integer(), nullable=True),
        sa.Column('q5', sa.Integer(), nullable=True),
        sa.Column('q6', sa.Integer(), nullable=True),
        sa.Column('q7', sa.Integer(), nullable=True),
        sa.Column('q8', sa.Integer(), nullable=True),
        sa.Column('q9', sa.Integer(), nullable=True),
        sa.Column('q10', sa.Integer(), nullable=True),
        sa.Column('q11', sa.Integer(), nullable=True),
        sa.Column('q12', sa.Integer(), nullable=True),
        sa.Column('q13', sa.Integer(), nullable=True),
        sa.Column('q14', sa.Integer(), nullable=True),
        sa.Column('q15', sa.Integer(), nullable=True),
        sa.Column('q16', sa.Integer(), nullable=True),
        sa.Column('q17', sa.Integer(), nullable=True),
        sa.Column('q18', sa.Integer(), nullable=True),
        sa.Column('q19', sa.Integer(), nullable=True),
        sa.Column('q20', sa.Integer(), nullable=True),
        sa.Column('q21', sa.Integer(), nullable=True),
        sa.Column('q22', sa.Integer(), nullable=True),
        sa.Column('q23', sa.Integer(), nullable=True),
        sa.Column('q24', sa.Integer(), nullable=True),
        sa.Column('q25', sa.Integer(), nullable=True),
        sa.Column('q26', sa.Integer(), nullable=True),
        sa.Column('strategy_pct', sa.Float(), nullable=True),
        sa.Column('activities_pct', sa.Float(), nullable=True),
        sa.Column('outputs_pct', sa.Float(), nullable=True),
        sa.Column('outcomes_pct', sa.Float(), nullable=True),
        sa.Column('quality_pct', sa.Float(), nullable=True),
        sa.Column('learning_pct', sa.Float(), nullable=True),
        sa.Column('total_score', sa.Float(), nullable=True),
        sa.Column('total_pct', sa.Float(), nullable=True),
        sa.Column('letter_grade', sa.String(length=2), nullable=True),
        sa.Column('analyst_id', sa.String(length=36), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['charity_id'], ['charity.id']),
        sa.ForeignKeyConstraint(['cycle_id'], ['evaluation_cycle.id']),
        sa.ForeignKeyConstraint(['analyst_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('srss_historical',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('charity_id', sa.String(length=36), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('total_pct', sa.Float(), nullable=True),
        sa.Column('letter_grade', sa.String(length=2), nullable=True),
        sa.Column('strategy_pct', sa.Float(), nullable=True),
        sa.Column('activities_pct', sa.Float(), nullable=True),
        sa.Column('outputs_pct', sa.Float(), nullable=True),
        sa.Column('outcomes_pct', sa.Float(), nullable=True),
        sa.Column('quality_pct', sa.Float(), nullable=True),
        sa.Column('learning_pct', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['charity_id'], ['charity.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('profile_content',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('charity_id', sa.String(length=36), nullable=False),
        sa.Column('section_type', sa.String(length=30), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['charity_id'], ['charity.id']),
        sa.ForeignKeyConstraint(['author_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('profile_content')
    op.drop_table('srss_historical')
    op.drop_table('srss_score')
