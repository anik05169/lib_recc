import os
import warnings
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()


def _is_production_host() -> bool:
    """True when running on a common PaaS (Render, Railway, etc.)."""
    return bool(
        os.getenv("RENDER")
        or os.getenv("RAILWAY_ENVIRONMENT")
        or os.getenv("ENV", "").lower() == "production"
    )


def get_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY")
    if not secret:
        raise RuntimeError(
            "JWT secret is not configured. Set JWT_SECRET or SECRET_KEY before starting the backend."
        )
    if secret in ("change-me-to-a-long-random-string", "changeme", "secret"):
        warnings.warn(
            "JWT_SECRET is still a placeholder. Set a strong random value in production.",
            stacklevel=2,
        )
    return secret


def validate_runtime_config():
    # Fail fast on startup instead of silently using an insecure fallback.
    get_jwt_secret()

    if _is_production_host():
        mongo_uri = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI") or ""
        if not mongo_uri or mongo_uri.startswith("mongodb://localhost"):
            raise RuntimeError(
                "MONGODB_URI must be set to your Atlas connection string in production."
            )

        cors = os.getenv("ALLOWED_ORIGINS") or os.getenv("FRONTEND_URL")
        if not cors:
            warnings.warn(
                "ALLOWED_ORIGINS is not set. Browser requests from your Vercel URL will be "
                "blocked by CORS. Set ALLOWED_ORIGINS=https://your-app.vercel.app",
                stacklevel=2,
            )

        pinecone_key = os.getenv("PINECONE_API_KEY", "").strip()
        pinecone_index = os.getenv("PINECONE_INDEX_NAME", "").strip()
        if not pinecone_key or not pinecone_index:
            warnings.warn(
                "PINECONE_API_KEY and PINECONE_INDEX_NAME are not set. "
                "Recommendations will return 503 until Pinecone is configured and synced.",
                stacklevel=2,
            )


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
