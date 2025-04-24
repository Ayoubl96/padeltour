from app.models.base import *

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
    tournament_courts = relationship("TournamentCourt", back_populates="court") 