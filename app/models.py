from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSON
from .db import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from .tools import generate_random_numeric_string

class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    login = Column(String(8), primary_key=True, default=lambda: generate_random_numeric_string(8))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'), onupdate=text('NOW()'))
    phone_number = Column(String, nullable=True)
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
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'), onupdate=text('NOW()'))
    company = relationship("Company", back_populates="tournaments")


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

    player_companies = relationship("PlayerCompany", back_populates="player")

class PlayerCompany(Base):
    __tablename__ = "player_company"
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)

    company = relationship("Company", back_populates="player_companies")
    player = relationship("Player", back_populates="player_companies")
