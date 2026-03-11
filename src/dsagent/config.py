"""DSAgent Ralph - Configuration"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # App
    app_name: str = "DSAgent Ralph"
    debug: bool = False
    
    # Database
    database_url: str = "postgresql://dsagent:dsagent@localhost:5432/dsagent"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # LLM
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    default_model: str = "claude-sonnet-4-20250514"
    
    # Jupyter
    jupyter_kernel_timeout: int = 300
    
    # Storage
    artifacts_path: str = "/artifacts"
    s3_bucket: str = ""
    s3_endpoint_url: str = ""
    
    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
