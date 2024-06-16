from fastapi import FastAPI
from routes.posts import router as posts_router
from routes.results import router as results_router

app = FastAPI()

app.include_router(posts_router, prefix="/posts")
app.include_router(results_router, prefix="/results")
