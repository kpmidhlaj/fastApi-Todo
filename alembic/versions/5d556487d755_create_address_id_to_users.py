"""create address_id to users

Revision ID: 5d556487d755
Revises: d870156b692f
Create Date: 2025-03-20 15:09:35.571498

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '5d556487d755'
down_revision: Union[str, None] = 'd870156b692f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('address_id', sa.Integer(), nullable=True))
    op.create_foreign_key('address_users_fk', 'users', 'address', ['address_id'],
                          ['id'], ondelete="CASCADE")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('address_users_fk', 'users', type_='foreignkey')
    op.drop_column('users', 'address_id')
