"""Add VAT number to companies table

Revision ID: vat_num_comp
Revises: f1x_brackets
Create Date: 2025-01-27 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'vat_num_comp'
down_revision: Union[str, None] = '32115f05f274'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add VAT number column to companies table
    op.add_column('companies', sa.Column('vat_number', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove VAT number column from companies table
    op.drop_column('companies', 'vat_number') 