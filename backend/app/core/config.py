import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ENVIRONMENT: str = "dev"
    PROJECT_NAME: str = "KnowledgeOS"
    
    # Database (Enforced dynamically, no production hardcoding)
    DATABASE_URL: str
    
    # Security (Enforced dynamically, no production hardcoding)
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Google Gemini API (Enforced dynamically)
    GEMINI_API_KEY: str
    
    # Storage Configuration ("local" or "s3")
    STORAGE_PROVIDER: str = "local"
    LOCAL_STORAGE_PATH: str = "storage/uploads"
    
    # AWS S3 / Cloudflare R2
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: Optional[str] = None
    S3_ENDPOINT_URL: Optional[str] = None
    
    # CORS Origins (Comma separated strings)
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instantiate settings. Pydantic Settings will automatically fetch values from the system environment
# or the local .env file.
try:
    settings = Settings()
except Exception as e:
    # Print a clear message to help developers understand they need a .env file
    import sys
    print("\n[FATAL ERROR] Configuration settings validation failed.", file=sys.stderr)
    print("Please verify that a .env file is present or correct environment variables are set.", file=sys.stderr)
    print(f"Details: {str(e)}\n", file=sys.stderr)
    # Provide dummy settings during model import inspections if needed, else exit
    if "pytest" in sys.modules or os.getenv("ALEMBIC_RUN") == "true":
        # Fallback values for test and migration runners so that builds don't fail
        settings = Settings(
            DATABASE_URL="postgresql://postgres:postgrespassword@localhost:5432/knowledgeos",
            JWT_SECRET_KEY="test_jwt_secret_key_for_testing_purposes_only",
            GEMINI_API_KEY="dummy_gemini_api_key"
        )
    else:
        sys.exit(1)
