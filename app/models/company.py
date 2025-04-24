from app.models.base import *
from app.utils.string_utils import generate_random_numeric_string

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