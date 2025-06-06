"""Add email verification table

Revision ID: 6fb34752e3a6
Revises: e4c64ef922f0
Create Date: 2025-05-27 23:37:26.738915

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6fb34752e3a6'
down_revision: Union[str, None] = 'e4c64ef922f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('email_verifications',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('code', sa.String(length=6), nullable=False),
    sa.Column('registration_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=True),
    sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('attempts', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('email_verifications')
    # ### end Alembic commands ###
