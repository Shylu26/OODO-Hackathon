"""Application configuration — reads from environment or uses defaults."""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Central config consumed by database, auth, and route modules."""

    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME: str = os.getenv("DB_NAME", "transit_ops")
    JWT_SECRET: str = os.getenv(
        "JWT_SECRET", "transit-ops-hackathon-secret-key-2024"
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 24


settings = Settings()
