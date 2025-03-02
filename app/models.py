from sqlalchemy import Column, ForeignKey, Integer, String, text, Text
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import TIMESTAMP
from .db import Base
from .tools import generate_random_numeric_string
from sqlalchemy import UniqueConstraint


class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    login = Column(String(8), primary_key=True, default=lambda:generate_random_numeric_string(8))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'), onupdate=text('NOW()'))
    phone_number = Column(String, nullable=True)

    # Relationships
    courts = relationship("Court", back_populates="company")
    tournaments = relationship("Tournament", back_populates="company")
    player_companies = relationship("PlayerCompany", back_populates="company")


class Court(Base):
    __tablename__ = "courts"
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(String, nullable=False)
    images = Column(JSON, nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'), onupdate=text('NOW()'))

    # Relationships
    company = relationship("Company", back_populates="courts")


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


class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(String, nullable=True)
    surname = Column(String, nullable=True)
    nickname = Column(String, nullable=False)
    number = Column(Integer, nullable=True)
    email = Column(String, nullable=True)
    picture = Column(JSON, nullable=True)
    playtomic_id = Column(Integer, nullable=True, unique=True)
    level = Column(Integer, nullable=True)
    gender = Column(Integer, nullable=False)

    # Relationships
    player_companies = relationship("PlayerCompany", back_populates="player")
    tournament_players = relationship("TournamentPlayer", back_populates="player")
    couples_as_first = relationship(
        "TournamentCouple",
        foreign_keys="[TournamentCouple.first_player_id]",
        back_populates="first_player"
    )
    couples_as_second = relationship(
        "TournamentCouple",
        foreign_keys="[TournamentCouple.second_player_id]",
        back_populates="second_player"
    )


class PlayerCompany(Base):
    __tablename__ = "player_company"
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)

    # Relationships
    company = relationship("Company", back_populates="player_companies")
    player = relationship("Player", back_populates="player_companies")


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

    # Relationships
    tournament = relationship("Tournament", back_populates="matches")
    couple1 = relationship("TournamentCouple", foreign_keys=[couple1_id])
    couple2 = relationship("TournamentCouple", foreign_keys=[couple2_id])
    winner = relationship("TournamentCouple", foreign_keys=[winner_couple_id])


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

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('tournament_id', 'couple_id', name='unique_couple_stats'),
    )

    # Relationships
    tournament = relationship("Tournament", back_populates="all_couple_stats")
    couple = relationship("TournamentCouple", back_populates="stats")