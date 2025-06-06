"""Create all tables

Revision ID: b570e9482c94
Revises: 1e4302b6dd91
Create Date: 2025-04-09 21:23:16.569531

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b570e9482c94'
down_revision: Union[str, None] = '1e4302b6dd91'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('players',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('surname', sa.String(), nullable=True),
    sa.Column('nickname', sa.String(), nullable=False),
    sa.Column('number', sa.Integer(), nullable=True),
    sa.Column('email', sa.String(), nullable=True),
    sa.Column('picture', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('playtomic_id', sa.Integer(), nullable=True),
    sa.Column('level', sa.Integer(), nullable=True),
    sa.Column('gender', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('playtomic_id')
    )
    op.create_table('player_company',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('player_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.ForeignKeyConstraint(['player_id'], ['players.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tournaments',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('images', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('start_date', sa.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('end_date', sa.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('players_number', sa.Integer(), nullable=False),
    sa.Column('full_description', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tournament_couple',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('tournament_id', sa.Integer(), nullable=False),
    sa.Column('first_player_id', sa.Integer(), nullable=False),
    sa.Column('second_player_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('name', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['first_player_id'], ['players.id'], ),
    sa.ForeignKeyConstraint(['second_player_id'], ['players.id'], ),
    sa.ForeignKeyConstraint(['tournament_id'], ['tournaments.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tournament_players',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('tournament_id', sa.Integer(), nullable=False),
    sa.Column('player_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['player_id'], ['players.id'], ),
    sa.ForeignKeyConstraint(['tournament_id'], ['tournaments.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('couple_stats',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('tournament_id', sa.Integer(), nullable=False),
    sa.Column('couple_id', sa.Integer(), nullable=False),
    sa.Column('matches_played', sa.Integer(), nullable=True),
    sa.Column('matches_won', sa.Integer(), nullable=True),
    sa.Column('matches_lost', sa.Integer(), nullable=True),
    sa.Column('matches_drawn', sa.Integer(), nullable=True),
    sa.Column('games_won', sa.Integer(), nullable=True),
    sa.Column('games_lost', sa.Integer(), nullable=True),
    sa.Column('total_points', sa.Integer(), nullable=True),
    sa.Column('last_updated', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=True),
    sa.ForeignKeyConstraint(['couple_id'], ['tournament_couple.id'], ),
    sa.ForeignKeyConstraint(['tournament_id'], ['tournaments.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tournament_id', 'couple_id', name='unique_couple_stats')
    )
    op.create_table('matches',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('tournament_id', sa.Integer(), nullable=False),
    sa.Column('couple1_id', sa.Integer(), nullable=False),
    sa.Column('couple2_id', sa.Integer(), nullable=False),
    sa.Column('winner_couple_id', sa.Integer(), nullable=True),
    sa.Column('games', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    sa.ForeignKeyConstraint(['couple1_id'], ['tournament_couple.id'], ),
    sa.ForeignKeyConstraint(['couple2_id'], ['tournament_couple.id'], ),
    sa.ForeignKeyConstraint(['tournament_id'], ['tournaments.id'], ),
    sa.ForeignKeyConstraint(['winner_couple_id'], ['tournament_couple.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('matches')
    op.drop_table('couple_stats')
    op.drop_table('tournament_players')
    op.drop_table('tournament_couple')
    op.drop_table('tournaments')
    op.drop_table('player_company')
    op.drop_table('players')
    # ### end Alembic commands ###
