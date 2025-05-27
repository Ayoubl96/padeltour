"""Merge email verification and tournament brackets fix

Revision ID: 32115f05f274
Revises: 6fb34752e3a6, f1x_brackets
Create Date: 2025-05-27 23:55:24.808704

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '32115f05f274'
down_revision: Union[str, None] = ('6fb34752e3a6', 'f1x_brackets')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
