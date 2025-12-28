from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from database import Base

class Image(Base):
    __tablename__ = "images"

    id = Column(String, primary_key=True, index=True) # SHA1 Hash
    path = Column(String, unique=True, index=True) # Relative path
    prompt = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
