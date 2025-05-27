"""Fix tournament brackets with null stage_id

Revision ID: f1x_brackets
Revises: e4c64ef922f0
Create Date: 2025-01-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1x_brackets'
down_revision: Union[str, None] = 'e4c64ef922f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Delete any tournament brackets that have null stage_id
    # These are orphaned records that shouldn't exist
    op.execute("DELETE FROM tournament_brackets WHERE stage_id IS NULL")


def downgrade() -> None:
    # No downgrade needed - we're just cleaning up invalid data
    pass 