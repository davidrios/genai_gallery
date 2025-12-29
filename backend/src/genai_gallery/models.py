from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Image(Base):
    __tablename__ = "images"

    id = Column(String, primary_key=True, index=True) # SHA1 Hash
    path = Column(String, unique=True, index=True) # Relative path
    prompt = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    metadata_items = relationship("ImageMetadata", back_populates="image", cascade="all, delete-orphan")

class ImageMetadata(Base):
    __tablename__ = "image_metadata"

    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(String, ForeignKey("images.id"))
    key = Column(String, index=True)
    value = Column(String, index=True)

    image = relationship("Image", back_populates="metadata_items")
