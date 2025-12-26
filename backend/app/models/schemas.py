from typing import Optional
from pydantic import BaseModel


class Book(BaseModel):
    book_id: int
    title: str
    description: str
    image_url: Optional[str] = None


class Rating(BaseModel):
    user_id: int
    book_id: int
    rating: int  # 1–5
