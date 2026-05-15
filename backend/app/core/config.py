import os
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()


def get_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY")
    if not secret:
        raise RuntimeError(
            "JWT secret is not configured. Set JWT_SECRET or SECRET_KEY before starting the backend."
        )
    return secret


def validate_runtime_config():
    # Fail fast on startup instead of silently using an insecure fallback.
    get_jwt_secret()


def setup_cors(app):
    origins = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]
    
    env_origins = os.getenv("ALLOWED_ORIGINS") or os.getenv("FRONTEND_URL")
    if env_origins:
        origins.extend([o.strip() for o in env_origins.split(",")])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
