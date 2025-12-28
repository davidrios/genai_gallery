from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ImageMetadataBase(BaseModel):
    key: str
    value: str

    class Config:
        from_attributes = True

class ImageBase(BaseModel):
    id: str
    path: str
    prompt: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Image(ImageBase):
    metadata_items: List[ImageMetadataBase] = []

class PaginatedImageResponse(BaseModel):
    items: List[Image]
    total: int
    page: int
    size: int
    pages: int

