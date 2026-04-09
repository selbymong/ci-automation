"""Add financial_acquisition, cra_data_request, evaluation_note tables

Revision ID: 009
Revises: 008
Create Date: 2026-04-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '009'
down_revision: Union[str, None] = '008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('financial_acquisition',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('charity_id', sa.String(length=36), nullable=False),
        sa.Column('cycle_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('afs_online_checked_at', sa.Date(), nullable=True),
        sa.Column('afs_url', sa.String(length=500), nullable=True),
        sa.Column('rfi_sent_at', sa.Date(), nullable=True),
        sa.Column('rfi_2_sent_at', sa.Date(), nullable=True),
        sa.Column('phone_followup_at', sa.Date(), nullable=True),
        sa.Column('cra_request_at', sa.Date(), nullable=True),
        sa.Column('received_at', sa.Date(), nullable=True),
        sa.Column('financial_statement_url', sa.String(length=500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['charity_id'], ['charity.id']),
        sa.ForeignKeyConstraint(['cycle_id'], ['evaluation_cycle.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('cra_data_request',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('charity_id', sa.String(length=36), nullable=False),
        sa.Column('years_requested', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('requested_at', sa.Date(), nullable=True),
        sa.Column('received_at', sa.Date(), nullable=True),
        sa.Column('batch_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['charity_id'], ['charity.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('evaluation_note',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('charity_id', sa.String(length=36), nullable=False),
        sa.Column('cycle_id', sa.String(length=36), nullable=True),
        sa.Column('note_type', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('author_id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['user.id']),
        sa.ForeignKeyConstraint(['charity_id'], ['charity.id']),
        sa.ForeignKeyConstraint(['cycle_id'], ['evaluation_cycle.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('evaluation_note')
    op.drop_table('cra_data_request')
    op.drop_table('financial_acquisition')
