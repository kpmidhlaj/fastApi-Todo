"""Add apt num column to address table

Revision ID: 8d393953efd1
Revises: 5d556487d755
Create Date: 2025-03-20 15:39:32.389284

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '8d393953efd1'
down_revision: Union[str, None] = '5d556487d755'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('address', sa.Column('apt_num', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('address', 'apt_num')
