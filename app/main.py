from fastapi import FastAPI
import uvicorn

from users.router import router as UsersRouter
from users.auth import router as AuthRouter
from videos.router import router as VideosRouter

app = FastAPI()

app.include_router(AuthRouter)
app.include_router(UsersRouter)
app.include_router(VideosRouter)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)