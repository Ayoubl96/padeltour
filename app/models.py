from sqlalchemy import Column, ForeignKey, Integer, String, column
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
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'))
    phone_number = Column(String, nullable=True)

