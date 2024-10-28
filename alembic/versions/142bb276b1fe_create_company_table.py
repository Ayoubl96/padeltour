"""Create company table

Revision ID: 142bb276b1fe
Revises: 
Create Date: 2024-10-28 21:18:51.647941

"""
from time import timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '142bb276b1fe'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('companies',
                    sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
                    sa.Column('email', sa.String, nullable=False, primary_key=False),
                    sa.Column('password', sa.String, nullable=False, primary_key=False),
                    sa.Column('phone_number', sa.String, nullable=False, primary_key=False),
                    sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, primary_key=False,
                              server_default=sa.text('NOW()')),
                    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True, primary_key=False,
                              server_default=sa.text('NOW()'))
                    )
    pass


def downgrade() -> None:
    pass
