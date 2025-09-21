from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/studentdb"
    JWT_SECRET_KEY: str = "supersecretkey"  # override in production with env
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # day
    MODEL_PATH: str = "models/risk_model.joblib"
    # thresholds (example)
    ATTENDANCE_THRESHOLD: float = 75.0  # percent
    TEST_DROP_THRESHOLD: float = 10.0   # percent drop triggering risk flag
    FEE_DELINQUENT_DAYS: int = 30       # days past due
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
