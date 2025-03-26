import uuid
from datetime import datetime
from sqlalchemy.orm import relationship
from migrations.database.db.schemas import Base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, VARCHAR, Boolean, DateTime, Integer

class Users(Base):
    # Модель пользователя в системе
    # Содержит основную информацию о пользователе и его аутентификации
    __tablename__ = "users"

    # Уникальный идентификатор пользователя в формате UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Email пользователя (используется для входа и коммуникации)
    email = Column(String, unique=True, index=True)
    
    # Хешированный пароль (хранится в защищенном виде)
    hashed_password = Column(VARCHAR(255))
    
    # Флаг подтвержденного аккаунта
    confirmed = Column(Boolean, default=False)
    
    # Код подтверждения для проверки email/сброса пароля
    confiration_code = Column(String, nullable=True)
    
    # Токен обновления для JWT-аутентификации
    refresh_token = Column(String, nullable=True, index=True)
    
    # Дата и время создания аккаунта
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Дата и время истечения действия кода подтверждения
    expires_at = Column(DateTime, nullable=True)
    
    # Счетчик неудачных попыток входа (для защиты от перебора)
    login_attempts = Column(Integer, default=0)

    # Связь с анализами пользователя (один ко многим)
    analyses = relationship("Analysis", back_populates="user", cascade="all, delete-orphan")