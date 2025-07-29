"""Add match ordering fields

Revision ID: add_match_ordering_fields
Revises: f1x_brackets
Create Date: 2025-01-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_match_ordering_fields'
down_revision = 'f1x_brackets'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new ordering and display fields to matches table
    op.add_column('matches', sa.Column('display_order', sa.Integer(), nullable=True))
    op.add_column('matches', sa.Column('order_in_stage', sa.Integer(), nullable=True))
    op.add_column('matches', sa.Column('order_in_group', sa.Integer(), nullable=True))
    op.add_column('matches', sa.Column('bracket_position', sa.Integer(), nullable=True))
    op.add_column('matches', sa.Column('round_number', sa.Integer(), nullable=True))
    op.add_column('matches', sa.Column('priority_score', sa.Float(), nullable=True))
    
    # Create indexes for performance on ordering fields
    op.create_index('idx_matches_display_order', 'matches', ['display_order'])
    op.create_index('idx_matches_stage_order', 'matches', ['stage_id', 'order_in_stage'])
    op.create_index('idx_matches_group_order', 'matches', ['group_id', 'order_in_group'])
    op.create_index('idx_matches_bracket_position', 'matches', ['bracket_id', 'bracket_position'])
    op.create_index('idx_matches_round_number', 'matches', ['tournament_id', 'round_number'])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('idx_matches_round_number', table_name='matches')
    op.drop_index('idx_matches_bracket_position', table_name='matches')
    op.drop_index('idx_matches_group_order', table_name='matches')
    op.drop_index('idx_matches_stage_order', table_name='matches')
    op.drop_index('idx_matches_display_order', table_name='matches')
    
    # Drop columns
    op.drop_column('matches', 'priority_score')
    op.drop_column('matches', 'round_number')
    op.drop_column('matches', 'bracket_position')
    op.drop_column('matches', 'order_in_group')
    op.drop_column('matches', 'order_in_stage')
    op.drop_column('matches', 'display_order') 