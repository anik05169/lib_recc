from typing import Optional
from pydantic import BaseModel, EmailStr


class Book(BaseModel):
    book_id: int
    title: str
    description: str
    image_url: Optional[str] = None


class Rating(BaseModel):
    user_id: int
    book_id: int
    rating: int  # 1–5


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    user_id: str
    email: str
    name: str
