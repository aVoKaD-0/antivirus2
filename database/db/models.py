from sqlalchemy import Column, Integer, String, VARCHAR
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from db.schemas import Base 


class Users(Base):
    __tablename__ = "users"

    username = Column(String, unique=True, index=True)
    email = Column(String, primary_key=True, unique=True, index=True)
    hashed_password = Column(VARCHAR(255), index=True)

    items = relationship("Item", back_populates="owner")

class Analysis(Base):
    __tablename__ = "analysis"

    analysis_id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    timestamp = Column(String, index=True)
    status = Column(String, index=True)

    items = relationship("Item", back_populates="owner")

class Results(Base):
    __tablename__ = "results"

    analysis_id = Column(Integer, primary_key=True, index=True)
    file_activity = Column(JSONB, index=True)
    docker_output = Column(String, index=True)
    results = Column(String, index=True)

    items = relationship("Item", back_populates="owner")

    