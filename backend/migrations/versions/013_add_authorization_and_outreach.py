"""Add evaluation_authorization and charity_outreach tables

Revision ID: 013
Revises: 012
Create Date: 2026-04-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '013'
down_revision: Union[str, None] = '012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('evaluation_authorization',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('evaluation_id', sa.String(length=36), nullable=False),
        sa.Column('step', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('reviewer_id', sa.String(length=36), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('decided_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['evaluation_id'], ['evaluation.id']),
        sa.ForeignKeyConstraint(['reviewer_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('charity_outreach',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('evaluation_id', sa.String(length=36), nullable=False),
        sa.Column('charity_id', sa.String(length=36), nullable=False),
        sa.Column('profile_sent_at', sa.Date(), nullable=True),
        sa.Column('sent_to_email', sa.String(length=255), nullable=True),
        sa.Column('email_saved', sa.Boolean(), nullable=False),
        sa.Column('read_receipt', sa.Boolean(), nullable=False),
        sa.Column('response_received', sa.Boolean(), nullable=False),
        sa.Column('response_received_at', sa.Date(), nullable=True),
        sa.Column('call_scheduled', sa.Boolean(), nullable=False),
        sa.Column('call_scheduled_at', sa.Date(), nullable=True),
        sa.Column('charity_adds_content', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('analyst_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['evaluation_id'], ['evaluation.id']),
        sa.ForeignKeyConstraint(['charity_id'], ['charity.id']),
        sa.ForeignKeyConstraint(['analyst_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('charity_outreach')
    op.drop_table('evaluation_authorization')
