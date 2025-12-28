from fastapi import APIRouter, HTTPException, status, Depends
from app.models.schemas import UserRegister, UserLogin, Token, UserResponse
from app.core.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_user_by_email,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.db.mongo import get_mongo_db
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
def register(user_data: UserRegister):
    """Register a new user."""
    db = get_mongo_db()
    
    # Check if user already exists
    if get_user_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Create user document
    user_doc = {
        "email": user_data.email,
        "password": hashed_password,
        "name": user_data.name,
    }
    
    # Insert user
    result = db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    return {
        "user_id": user_id,
        "email": user_data.email,
        "name": user_data.name,
    }


@router.post("/login", response_model=Token)
def login(user_data: UserLogin):
    """Login and get access token."""
    # Get user from database
    user = get_user_by_email(user_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not verify_password(user_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user["_id"])},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information."""
    return {
        "user_id": str(current_user["_id"]),
        "email": current_user["email"],
        "name": current_user["name"],
    }

