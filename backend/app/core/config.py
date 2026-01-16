import os
from fastapi.middleware.cors import CORSMiddleware

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
