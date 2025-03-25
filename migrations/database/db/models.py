from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from migrations.database.db.schemas import Base
from sqlalchemy import Column, Integer, String, ForeignKey

# Модель Users находится в другом модуле, используем строковое имя класса для отложенной загрузки
# from app.domain.models.user import Users  # Не импортируем напрямую во избежание циклических импортов

class Analysis(Base):
    __tablename__ = "analysis"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    filename = Column(String)
    timestamp = Column(String)
    status = Column(String)
    analysis_id = Column(UUID(as_uuid=True), unique=True)

    # Используем строковое имя класса и имя модуля для отложенной загрузки
    user = relationship("Users", foreign_keys=[user_id], back_populates="analyses")

    result = relationship("Results", back_populates="analysis", uselist=False)

class Results(Base):
    __tablename__ = "results"

    analysis_id = Column(UUID(as_uuid=True), ForeignKey('analysis.analysis_id', ondelete="CASCADE"), primary_key=True)
    file_activity = Column(String)
    docker_output = Column(String)
    results = Column(String)

    analysis = relationship("Analysis", back_populates="result")