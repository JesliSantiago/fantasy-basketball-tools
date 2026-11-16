from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.routers import draft, health, rankings

app = FastAPI(title="Fantasy Basketball Tools API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(rankings.router, prefix="/api")
app.include_router(draft.router, prefix="/api")
