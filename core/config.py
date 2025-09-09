# app/core/config.py
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "Bola Marcada"
    API_V1_STR: str = "/api/v1"

    POSTGRES_SERVER: str = Field(..., env="POSTGRES_SERVER")
    POSTGRES_USER: str = Field(..., env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(..., env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field(..., env="POSTGRES_DB")
    DATABASE_URL: Optional[str] = None

    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60, env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"

    def assemble_db_connection(self) -> str:

        return (
            self.DATABASE_URL
            or f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
        )


settings = Settings()
