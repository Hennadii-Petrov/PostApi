from fastapi import status, HTTPException, APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from .. import schema, models
from ..database import get_db
from ..oauth2 import get_current_user


router = APIRouter(prefix="/posts", tags=["Posts"], redirect_slashes=False)

@router.get('', response_model=list[schema.PostWithVotes])
async def get_posts(db: AsyncSession = Depends(get_db), current_user: int = Depends(get_current_user), limit: int = 10, skip: int = 0, search: str = ""):
    stmt = select(
        models.Post,
        func.count(models.Vote.post_id).label("votes")
    ).outerjoin(
        models.Vote, models.Vote.post_id == models.Post.id
    ).group_by(
        models.Post.id
    ).filter(
        models.Post.title.contains(search)
    ).limit(limit).offset(skip)
    
    result = await db.execute(stmt)
    posts = result.all()
    return posts

@router.post('', status_code=status.HTTP_201_CREATED, response_model=schema.PostResponse)
async def create_post(post: schema.PostCreate, db: AsyncSession = Depends(get_db), current_user: int = Depends(get_current_user)):
    new_post = models.Post(
        owner_id=current_user.id,
        **post.model_dump()
    )
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)
    return new_post

@router.get('/{id}', response_model=schema.PostResponse)
async def get_post(id: int, db: AsyncSession = Depends(get_db), current_user: int = Depends(get_current_user)):
    stmt = select(models.Post).filter(models.Post.id == id)
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()
    if post:
        return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

@router.delete('/{id}')
async def delete_post(id: int, db: AsyncSession = Depends(get_db), current_user: int = Depends(get_current_user)):
    stmt = select(models.Post).filter(models.Post.id == id)
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    if post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this post")
    await db.delete(post)
    await db.commit()
    return {"message": "Post deleted successfully"}

@router.put('/{id}', response_model=schema.PostResponse)
async def update_post(id: int, updated_post: schema.PostCreate, db: AsyncSession = Depends(get_db), current_user: int = Depends(get_current_user)):
    stmt = select(models.Post).filter(models.Post.id == id)
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()

    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    if post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this post")
    
    for key, value in updated_post.model_dump().items():
        setattr(post, key, value)
    await db.commit()
    await db.refresh(post)
    return post


