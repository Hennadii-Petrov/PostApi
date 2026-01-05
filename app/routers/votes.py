from fastapi import HTTPException, APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .. import schema, models
from ..database import get_db
from ..oauth2 import get_current_user


router = APIRouter(prefix="/votes", tags=["Votes"], redirect_slashes=False)

@router.post('/', status_code=201)
async def vote(vote: schema.Vote, db: AsyncSession = Depends(get_db), current_user: int = Depends(get_current_user)):
    stmt = select(models.Post).filter(models.Post.id == vote.post_id)
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    vote_stmt = select(models.Vote).filter(
        models.Vote.post_id == vote.post_id,
        models.Vote.user_id == current_user.id
    )
    vote_result = await db.execute(vote_stmt)
    found_vote = vote_result.scalar_one_or_none()
    
    if vote.dir == 1:
        if found_vote:
            raise HTTPException(status_code=409, detail="You have already voted on this post")
        new_vote = models.Vote(post_id=vote.post_id, user_id=current_user.id)
        db.add(new_vote)
        await db.commit()
        return {"message": "Vote added successfully"}
    else:
        if not found_vote:
            raise HTTPException(status_code=404, detail="Vote does not exist")
        await db.delete(found_vote)
        await db.commit()
        return {"message": "Vote removed successfully"}
    
@router.get('/', response_model=list[schema.VoteResponse])
async def get_votes(db: AsyncSession = Depends(get_db), current_user: int = Depends(get_current_user)):
    stmt = select(models.Vote).filter(models.Vote.user_id == current_user.id)
    result = await db.execute(stmt)
    votes = result.scalars().all()
    return votes