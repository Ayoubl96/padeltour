"""merge match ordering and vat number changes

Revision ID: merge_final_heads
Revises: add_match_ordering_fields, vat_num_comp
Create Date: 2025-01-27 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'merge_final_heads'
down_revision: Union[str, None] = ('add_match_ordering_fields', 'vat_num_comp')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # This is a merge migration - no database changes needed
    # Both parent migrations have already been applied
    pass


def downgrade() -> None:
    # This is a merge migration - no database changes needed
    pass 