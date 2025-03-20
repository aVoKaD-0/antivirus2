from app.domain.models.user import Users
from sqlalchemy import Column, Integer, String, VARCHAR, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from migrations.database.db.schemas import Base

class Analysis(Base):
    __tablename__ = "analysis"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    filename = Column(String)
    timestamp = Column(String)
    status = Column(String)
    analysis_id = Column(UUID(as_uuid=True), unique=True)

    # Связь с таблицей Users
    user = relationship("Users", back_populates="analyses")

    # Связь с таблицей Results
    result = relationship("Results", back_populates="analysis", uselist=False)

class Results(Base):
    __tablename__ = "results"

    analysis_id = Column(UUID(as_uuid=True), ForeignKey('analysis.analysis_id', ondelete="CASCADE"), primary_key=True)
    file_activity = Column(JSONB, index=True)
    docker_output = Column(String, index=True)
    results = Column(String, index=True)

    # Связь для удобного обращения к анализу из результата
    analysis = relationship("Analysis", back_populates="result")