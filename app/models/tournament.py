from app.models.base import *
from sqlalchemy import Boolean

class Tournament(Base):
    __tablename__ = "tournaments"
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    images = Column(JSON, nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    start_date = Column(TIMESTAMP(timezone=True), nullable=False)
    end_date = Column(TIMESTAMP(timezone=True), nullable=False)
    players_number = Column(Integer, nullable=False)
    full_description = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'), onupdate=text('NOW()'))

    # Relationships
    company = relationship("Company", back_populates="tournaments")
    tournament_players = relationship("TournamentPlayer", back_populates="tournament")
    couples = relationship("TournamentCouple", back_populates="tournament")
    matches = relationship("Match", back_populates="tournament")
    all_couple_stats = relationship("CoupleStats", back_populates="tournament")
    tournament_courts = relationship("TournamentCourt", back_populates="tournament")
    stages = relationship("TournamentStage", back_populates="tournament")


class TournamentStage(Base):
    __tablename__ = "tournament_stages"
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    name = Column(String, nullable=False)
    stage_type = Column(String, nullable=False)  # 'group' or 'elimination'
    order = Column(Integer, nullable=False)  # Order in the tournament flow
    config = Column(JSONB, nullable=False)  # Configuration JSON
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'), onupdate=text('NOW()'))
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    tournament = relationship("Tournament", back_populates="stages")
    groups = relationship("TournamentGroup", back_populates="stage")
    brackets = relationship("TournamentBracket", back_populates="stage")
    matches = relationship("Match", back_populates="stage")
    
    # Constraints
    __table_args__ = (
        # Unique constraint for stage order within a tournament
        UniqueConstraint('tournament_id', 'order', name='unique_stage_order_per_tournament'),
    )


class TournamentGroup(Base):
    __tablename__ = "tournament_groups"
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    stage_id = Column(Integer, ForeignKey("tournament_stages.id"), nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'), onupdate=text('NOW()'))
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    stage = relationship("TournamentStage", back_populates="groups")
    couples = relationship("TournamentGroupCouple", back_populates="group")
    matches = relationship("Match", back_populates="group")


class TournamentGroupCouple(Base):
    __tablename__ = "tournament_group_couples"
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    group_id = Column(Integer, ForeignKey("tournament_groups.id"), nullable=False)
    couple_id = Column(Integer, ForeignKey("tournament_couple.id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'), onupdate=text('NOW()'))
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    group = relationship("TournamentGroup", back_populates="couples")
    couple = relationship("TournamentCouple")
    
    # Constraints
    __table_args__ = (
        # Ensure a couple is only in one group per stage
        UniqueConstraint('group_id', 'couple_id', name='unique_couple_per_group'),
    )


class TournamentBracket(Base):
    __tablename__ = "tournament_brackets"
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    stage_id = Column(Integer, ForeignKey("tournament_stages.id"), nullable=False)
    bracket_type = Column(String, nullable=False)  # 'main', 'silver', 'bronze'
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'), onupdate=text('NOW()'))
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    stage = relationship("TournamentStage", back_populates="brackets")
    matches = relationship("Match", back_populates="bracket")
    
    # Constraints
    __table_args__ = (
        # Ensure unique bracket type per stage
        UniqueConstraint('stage_id', 'bracket_type', name='unique_bracket_type_per_stage'),
    )


class TournamentPlayer(Base):
    __tablename__ = "tournament_players"
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'), onupdate=text('NOW()'))
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    tournament = relationship("Tournament", back_populates="tournament_players")
    player = relationship("Player", back_populates="tournament_players")


class TournamentCouple(Base):
    __tablename__ = "tournament_couple"
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    first_player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    second_player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'), onupdate=text('NOW()'))
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    name = Column(String, nullable=False)

    # Relationships
    tournament = relationship("Tournament", back_populates="couples")
    first_player = relationship("Player", foreign_keys=[first_player_id], back_populates="couples_as_first")
    second_player = relationship("Player", foreign_keys=[second_player_id], back_populates="couples_as_second")
    stats = relationship("CoupleStats", back_populates="couple")


class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    couple1_id = Column(Integer, ForeignKey("tournament_couple.id"), nullable=False)
    couple2_id = Column(Integer, ForeignKey("tournament_couple.id"), nullable=False)
    winner_couple_id = Column(Integer, ForeignKey("tournament_couple.id"), nullable=True)
    games = Column(JSONB, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'), onupdate=text('NOW()'))
    
    # New stage, group and bracket fields
    stage_id = Column(Integer, ForeignKey("tournament_stages.id"), nullable=True)
    group_id = Column(Integer, ForeignKey("tournament_groups.id"), nullable=True)
    bracket_id = Column(Integer, ForeignKey("tournament_brackets.id"), nullable=True)
    
    # Scheduling fields
    court_id = Column(Integer, ForeignKey("courts.id"), nullable=True)
    scheduled_start = Column(TIMESTAMP(timezone=True), nullable=True)
    scheduled_end = Column(TIMESTAMP(timezone=True), nullable=True)
    is_time_limited = Column(Boolean, default=False)
    time_limit_minutes = Column(Integer, nullable=True)
    match_result_status = Column(String, nullable=True)  # 'completed', 'time_expired', 'forfeited'

    # Relationships
    tournament = relationship("Tournament", back_populates="matches")
    couple1 = relationship("TournamentCouple", foreign_keys=[couple1_id])
    couple2 = relationship("TournamentCouple", foreign_keys=[couple2_id])
    winner = relationship("TournamentCouple", foreign_keys=[winner_couple_id])
    stage = relationship("TournamentStage", back_populates="matches")
    group = relationship("TournamentGroup", back_populates="matches")
    bracket = relationship("TournamentBracket", back_populates="matches")
    court = relationship("Court")


class CoupleStats(Base):
    __tablename__ = "couple_stats"
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    couple_id = Column(Integer, ForeignKey("tournament_couple.id"), nullable=False)
    matches_played = Column(Integer, default=0)
    matches_won = Column(Integer, default=0)
    matches_lost = Column(Integer, default=0)
    matches_drawn = Column(Integer, default=0)
    games_won = Column(Integer, default=0)
    games_lost = Column(Integer, default=0)
    total_points = Column(Integer, default=0)
    last_updated = Column(TIMESTAMP(timezone=True), server_default=text('NOW()'), onupdate=text('NOW()'))
    
    # New group stats field
    group_id = Column(Integer, ForeignKey("tournament_groups.id"), nullable=True)

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('tournament_id', 'couple_id', 'group_id', name='unique_couple_stats'),
    )

    # Relationships
    tournament = relationship("Tournament", back_populates="all_couple_stats")
    couple = relationship("TournamentCouple", back_populates="stats")
    group = relationship("TournamentGroup")


class TournamentCourt(Base):
    __tablename__ = "tournament_courts"
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    court_id = Column(Integer, ForeignKey("courts.id"), nullable=False)
    availability_start = Column(TIMESTAMP(timezone=True), nullable=True)
    availability_end = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'), onupdate=text('NOW()'))
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    tournament = relationship("Tournament", back_populates="tournament_courts")
    court = relationship("Court", back_populates="tournament_courts")
    
    # Constraints
    __table_args__ = (
        # Ensure unique active court per tournament
        UniqueConstraint('tournament_id', 'court_id', name='unique_active_tournament_court'),
    ) 