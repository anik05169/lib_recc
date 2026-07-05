from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator


class Book(BaseModel):
    book_id: Optional[int] = None  # Auto-generated if not provided
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

    @field_validator('password')
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class AiSuggestionRequest(BaseModel):
    description: str

    @field_validator("description")
    @classmethod
    def validate_description(cls, v):
        text = v.strip()
        if not text:
            raise ValueError("Description is required")
        return text


class Token(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    user_id: str
    email: str
    name: str
