"""
API Endpoints — Authentication.
"""

from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.auth import create_access_token, get_password_hash, verify_password
from app.core.config import settings
from app.core.logging_config import get_logger
from app.database.session import get_db
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserResponse

logger = get_logger(__name__)
router = APIRouter(tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate, db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Register a new user.
    """
    # Check if username or email already exists
    stmt = select(User).where(
        (User.username == user_in.username) | (User.email == user_in.email)
    )
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(
            status_code=400,
            detail="The username or email is already registered in the system.",
        )

    # Create new user
    db_user = User(
        username=user_in.username,
        email=user_in.email,
        full_name=user_in.full_name,
        role="farmer",
        # Store password hash in notes for simplicity in this demo (usually a dedicated column is better)
        notes=get_password_hash(user_in.password),
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


@router.post("/login", response_model=Token)
async def login_access_token(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    # Fetch user
    stmt = select(User).where(User.username == form_data.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    # We stored the hashed password in 'notes' for this implementation
    if not user or not user.notes or not verify_password(form_data.password, user.notes):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password",
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        subject=user.username, expires_delta=access_token_expires
    )
    
    logger.info(f"User '{user.username}' logged in successfully.")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
