from routes.posts import router as posts_router
from routes.results import router as results_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi import FastAPI, middleware
middleware = [
    middleware.Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    ),
    middleware.Middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"],
    )
]

app = FastAPI(middleware=middleware)

app.include_router(posts_router, prefix="/posts")
app.include_router(results_router, prefix="/results")
