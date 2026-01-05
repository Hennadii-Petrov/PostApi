
from fastapi import status, HTTPException, APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .. import schema, models, utils
from ..database import get_db

router = APIRouter(prefix="/users", tags=["Users"], redirect_slashes=False)

@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schema.UserResponse)
async def create_user(user: schema.UserCreate, db: AsyncSession = Depends(get_db)):
    stmt = select(models.User).filter(models.User.email == user.email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    # No password length limitation with Argon2
    hashed_password = utils.hash_password(user.password)
    
    new_user = models.User(
        email=user.email,
        password=hashed_password
    )
    db.add(new_user)
    await db.commit()
    # Merge the object back into the session after commit
    new_user = await db.merge(new_user)
    await db.refresh(new_user)
    return new_user

@router.get('/{user_id}', response_model=schema.UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(models.User).filter(models.User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user