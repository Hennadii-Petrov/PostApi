
from fastapi import FastAPI
from . import  models
from .database import engine
from .routers import auth, posts, users, votes


app = FastAPI()


@app.on_event("startup")
async def on_startup() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await engine.dispose()


app.include_router(posts.router)
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(votes.router)




