from sqlalchemy import Column, ForeignKey, Integer, String, text, Text
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy import UniqueConstraint
from app.db.database import Base 