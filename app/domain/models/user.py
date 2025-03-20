from sqlalchemy import Column, String, VARCHAR, Boolean
from migrations.database.db.schemas import Base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Users(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(VARCHAR(255), index=True)
    confirmed = Column(Boolean, default=False)
    confiration_code = Column(String, nullable=True)
    refresh_token = Column(String, nullable=True)

    # Связь для удобного обращения к анализам пользователя
    analyses = relationship("Analysis", back_populates="user", cascade="all, delete-orphan")