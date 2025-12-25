from fastapi import FastAPI
from app.core.config import setup_cors
from app.routes import books, users, ratings
from app.startup import train_on_startup

app = FastAPI(title="Personal Library System")

setup_cors(app)

app.include_router(books.router)
app.include_router(users.router)
app.include_router(ratings.router)

# app.add_event_handler("startup", train_on_startup)

@app.get("/")
def root():
    return {"message": "Personal Library API running"}
