from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).parent.parent.parent / ".env"


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE if ENV_FILE.exists() else None,
        case_sensitive=True,
        extra="ignore",
    )

    # PostgresSQL
    postgres_user: str = Field(validation_alias="POSTGRES_USER")
    postgres_password: SecretStr = Field(validation_alias="POSTGRES_PASSWORD")
    postgres_host: str = Field(validation_alias="POSTGRES_HOST")
    postgres_port: str = Field(validation_alias="POSTGRES_PORT")
    postgres_db_name: str = Field(validation_alias="POSTGRES_DB_NAME")

    redis_password: SecretStr = Field(validation_alias="REDIS_PASSWORD")
    redis_host: str = Field(validation_alias="REDIS_HOST")
    redis_port: str = Field(validation_alias="REDIS_PORT")
    redis_db: str = Field(validation_alias="REDIS_AUTH_DB")

    @property
    def redis_url(self) -> str:
        return (
            f"redis://:{self.redis_password.get_secret_value()}"
            f"@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        )


settings = Config()  # type: ignore
