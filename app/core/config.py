"""Application settings loaded from the project .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	app_name: str = "Retail Return Reasoning Agent"
	database_url: str = "postgresql+psycopg://retail_agent:1234@localhost:5432/retail_agent_db"
	secret_key: str = ""
	access_token_expire_minutes: int = 60
	initial_admin_email: str = "jerrill2003@gmail.com"
	initial_admin_password: str = "1234"
	return_rate_threshold: float = 0.10
	gemini_api_key: str = ""
	gemini_chat_model: str = "gemini-3.8-flash"
	gemini_embedding_model: str = "gemini-embedding-001"
	app_base_url: str = "http://127.0.0.1:8000/app/"
	smtp_host: str = ""
	smtp_port: int = 587
	smtp_username: str = ""
	smtp_password: str = ""
	smtp_from_email: str = ""
	smtp_use_starttls: bool = True
	password_reset_token_minutes: int = 30
	chunk_size: int = 700
	chunk_overlap: int = 100

	model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
	return Settings()


settings = get_settings()
