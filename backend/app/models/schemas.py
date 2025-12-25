from pydantic import BaseModel

class Book(BaseModel):
    book_id: int
    title: str
    description: str
    image_url: str


class Rating(BaseModel):
    user_id: int
    book_id: int
    rating: int  # 1–5
