"""add tournament courts

Revision ID: ee9ea1cc839d
Revises: b570e9482c94
Create Date: 2025-04-24 00:32:11.328094

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'ee9ea1cc839d'
down_revision: Union[str, None] = 'b570e9482c94'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create tournament_courts table
    op.create_table('tournament_courts',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('tournament_id', sa.Integer(), nullable=False),
        sa.Column('court_id', sa.Integer(), nullable=False),
        sa.Column('availability_start', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('availability_end', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), onupdate=sa.text('NOW()'), nullable=False),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tournament_id'], ['tournaments.id'], ),
        sa.ForeignKeyConstraint(['court_id'], ['courts.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tournament_id', 'court_id', name='unique_active_tournament_court')
    )
    
    # Create index on tournament_id for faster queries
    op.create_index(op.f('ix_tournament_courts_tournament_id'), 'tournament_courts', ['tournament_id'], unique=False)
    
    # Create index on court_id for faster queries
    op.create_index(op.f('ix_tournament_courts_court_id'), 'tournament_courts', ['court_id'], unique=False)


def downgrade() -> None:
    # Drop the indices first
    op.drop_index(op.f('ix_tournament_courts_court_id'), table_name='tournament_courts')
    op.drop_index(op.f('ix_tournament_courts_tournament_id'), table_name='tournament_courts')
    
    # Drop the table
    op.drop_table('tournament_courts')
