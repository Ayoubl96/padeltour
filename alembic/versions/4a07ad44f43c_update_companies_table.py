"""Update companies table

Revision ID: 4a07ad44f43c
Revises: 142bb276b1fe
Create Date: 2024-10-29 18:18:37.765562

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a07ad44f43c'
down_revision: Union[str, None] = '142bb276b1fe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('companies', sa.Column('name', sa.String(), nullable=False))
    op.add_column('companies', sa.Column('address', sa.String(), nullable=False))
    op.add_column('companies', sa.Column('login', sa.String(8), nullable=False, primary_key=True))


    pass


def downgrade() -> None:
    pass
