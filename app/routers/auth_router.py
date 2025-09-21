from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from .. import crud
from ..schemas import UserCreate, Token, UserLogin, UserRegisterResponse # Updated imports
from ..database import get_db
from ..auth import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserRegisterResponse) # Updated response_model
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await crud.get_user_by_username(db, user.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed = hash_password(user.password)
    created = await crud.create_user(db, user, hashed)
    return {"message": "user created", "username": created.username}

@router.post("/token", response_model=Token)
async def login_for_access_token(
    user_credentials: UserLogin, # Updated parameter
    db: AsyncSession = Depends(get_db)
):
    """
    Expect JSON body with {"username": "...", "password": "..."}
    """
    db_user = await crud.get_user_by_username(db, user_credentials.username)
    if not db_user or not verify_password(
        user_credentials.password, db_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid credentials"
        )
    
    token = create_access_token({"sub": db_user.username, "role": db_user.role})
    return {"access_token": token, "token_type": "bearer"}