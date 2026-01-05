from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.security import OAuth2PasswordRequestForm
from ..database import get_db
from ..models import User
from ..utils import verify_password
from ..oauth2 import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"], redirect_slashes=False)

@router.post('/login')
async def login(user: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    stmt = select(User).filter(User.email == user.username)
    result = await db.execute(stmt)
    found_user = result.scalar_one_or_none()

    if not found_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")
    
    if not verify_password(user.password, found_user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")
    
    access_token = create_access_token(data={"user_id": found_user.id})
    return {"access_token": access_token, "token_type": "bearer"}