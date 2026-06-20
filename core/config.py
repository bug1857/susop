import os

class Settings:
    PROJECT_NAME: str = "SustainOCPM Multi-Tenant API"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkeyforlocaldevelopmentsprint1")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days for development ease
    
    # Database Configuration
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "sustainocpm")
    
    @property
    def DATABASE_URL(self) -> str:
        # Fallback to local SQLite for out-of-the-box local testing if PG_HOST is not explicitly specified
        if os.getenv("USE_SQLITE", "true").lower() == "true":
            return "sqlite:///./sustainocpm.db"
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Central Insight Thresholds
    INSIGHT_THRESHOLDS: dict = {
        "carbon_hotspot": {
            "low": 100.0,
            "medium": 500.0,
            "high": 1000.0,
            "critical": 5000.0
        },
        "bottleneck_hours": 24.0,
        "conformance_rate": 0.10,
        "esg_score": 50.0,
        "completeness_score": 80.0
    }

settings = Settings()

