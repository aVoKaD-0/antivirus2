import uuid
from sqlalchemy.orm import relationship
from migrations.database.db.schemas import Base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, VARCHAR, Boolean, ForeignKey, DateTime
from datetime import datetime

class Users(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(VARCHAR(255))
    confirmed = Column(Boolean, default=False)
    confiration_code = Column(String, nullable=True)
    refresh_token = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    analyses = relationship("Analysis", back_populates="user", cascade="all, delete-orphan")