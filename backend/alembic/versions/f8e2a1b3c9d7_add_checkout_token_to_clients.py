"""add_checkout_token_to_clients

Revision ID: f8e2a1b3c9d7
Revises: d2cd997fdb65
Create Date: 2026-06-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f8e2a1b3c9d7'
down_revision: Union[str, Sequence[str], None] = 'd2cd997fdb65'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('clients', sa.Column('checkout_token', sa.String(length=36), nullable=True))
    op.create_unique_constraint('uq_clients_checkout_token', 'clients', ['checkout_token'])
    op.create_index(op.f('ix_clients_checkout_token'), 'clients', ['checkout_token'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_clients_checkout_token'), table_name='clients')
    op.drop_constraint('uq_clients_checkout_token', 'clients', type_='unique')
    op.drop_column('clients', 'checkout_token')
