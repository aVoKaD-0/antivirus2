from sqlalchemy import Column, String, VARCHAR
from database.db.schemas import Base
from sqlalchemy.orm import relationship


class Users(Base):
    __tablename__ = "users"

    username = Column(String, unique=True, index=True)
    email = Column(String, primary_key=True, unique=True, index=True)
    hashed_password = Column(VARCHAR(255), index=True)

    items = relationship("Item", back_populates="owner")