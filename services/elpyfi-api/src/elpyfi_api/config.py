# Real-time test!
# Still working...
# All done!
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ELPYFI_",
        env_file=".env",
        extra="ignore"  # Ignore extra fields in .env
    )
    
    database_url: str = "postgresql://elpyfi:password@localhost/elpyfi"
    api_keys: str = ""  # Comma-separated
    cors_origins: str = "http://localhost:3000"
    port: int = 9002


settings = Settings()
