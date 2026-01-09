#main.py

from fastapi import FastAPI
from threading import Thread

from app.core.config import setup_cors
from app.routes import books, users, ratings, auth
from app.startup import train_recommender_on_startup

from dotenv import load_dotenv
load_dotenv()


app = FastAPI(title="Personal Library System")

setup_cors(app)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(books.router)
app.include_router(ratings.router)


@app.get("/")
def root():
    return {"message": "Personal Library API running"}

@app.on_event("startup")
def on_startup():
    Thread(target=train_recommender_on_startup, daemon=True).start()

