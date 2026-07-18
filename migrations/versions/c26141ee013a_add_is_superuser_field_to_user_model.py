"""add is_superuser field to user model

Revision ID: c26141ee013a
Revises: 8d35ae1193f9
Create Date: 2025-05-24 08:20:08.248401

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c26141ee013a'
down_revision: Union[str, None] = '8d35ae1193f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
