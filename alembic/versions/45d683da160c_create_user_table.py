"""create user table

Revision ID: 45d683da160c
Revises: 51f05c6f1b6a
Create Date: 2024-10-21 00:14:53.020590

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '45d683da160c'
down_revision: Union[str, None] = '51f05c6f1b6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('companies', sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
                    sa.Column('name', sa.String(), nullable=False))
    pass


def downgrade() -> None:
    pass
