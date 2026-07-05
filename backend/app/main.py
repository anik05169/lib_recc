#main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from threading import Thread

from app.core.config import setup_cors, validate_runtime_config
from app.routes import books, users, ratings, auth
from app.services.recommender import is_model_ready
from app.startup import train_recommender_on_startup

validate_runtime_config()


@asynccontextmanager
async def lifespan(app):
    # Startup: train recommender in background
    Thread(target=train_recommender_on_startup, daemon=True).start()
    yield
    # Shutdown: cleanup if needed


app = FastAPI(title="Personal Library System", lifespan=lifespan)

setup_cors(app)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(books.router)
app.include_router(ratings.router)


@app.get("/")
def root():
    return {"message": "Personal Library API running"}


@app.get("/health")
def health():
    return {"status": "ok", "recommender_ready": is_model_ready()}
