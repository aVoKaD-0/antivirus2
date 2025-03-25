from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from migrations.database.db.schemas import Base
from sqlalchemy import Column, Integer, String, ForeignKey

class Analysis(Base):
    __tablename__ = "analysis"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    filename = Column(String)
    timestamp = Column(String)
    status = Column(String)
    analysis_id = Column(UUID(as_uuid=True), unique=True)

    user = relationship("Users", back_populates="analyses")

    result = relationship("Results", back_populates="analysis", uselist=False)

class Results(Base):
    __tablename__ = "results"

    analysis_id = Column(UUID(as_uuid=True), ForeignKey('analysis.analysis_id', ondelete="CASCADE"), primary_key=True)
    file_activity = Column(String)
    docker_output = Column(String)
    results = Column(String)

    analysis = relationship("Analysis", back_populates="result")