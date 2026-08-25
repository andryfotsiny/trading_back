"""add exit_reason and stop_loss_initial to trades

Revision ID: a3f1c8b92d47
Revises: 282921ef1d25
Create Date: 2026-08-25 17:10:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'a3f1c8b92d47'
down_revision: Union[str, None] = '282921ef1d25'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('trades', sa.Column('exit_reason', sa.String(), nullable=True))
    op.add_column('trades', sa.Column('stop_loss_initial', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('trades', 'stop_loss_initial')
    op.drop_column('trades', 'exit_reason')
