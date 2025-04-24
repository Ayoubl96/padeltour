from app.models.base import *

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