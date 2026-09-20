import os
from functools import lru_cache
from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8006
    LOG_LEVEL: str = "info"
    CORS_ORIGINS: str = "*"

    MODEL_ID: str = "Qwen/Qwen2.5-1.5B-Instruct"
    MODEL_REVISION: str = "main"
    QUANTIZATION: Optional[str] = "none"
    DTYPE: str = "auto"
    MAX_MODEL_LEN: int = 4096
    GPU_MEMORY_UTILIZATION: float = 0.85
    ENFORCE_EAGER: bool = True
    TENSOR_PARALLEL_SIZE: int = 1
    TRUST_REMOTE_CODE: bool = True
    HF_TOKEN: Optional[str] = None
    CACHE_DIR: Optional[str] = None

    ENABLE_FALLBACK_TRANSFORMERS_BACKEND: bool = True
    ENABLE_PREFIX_CACHING: bool = True
    ALLOW_CPU_FALLBACK: bool = False
    AUTO_LOAD_ON_STARTUP: bool = True

    DEFAULT_MAX_TOKENS: int = 512
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_TOP_P: float = 0.9
    DEFAULT_TOP_K: int = 50
    DEFAULT_REPETITION_PENALTY: float = 1.05
    DEFAULT_ENABLE_THINKING: bool = True

    CLOUDFLARE_TUNNEL_ENABLED: bool = True
    CLOUDFLARE_TUNNEL_TOKEN: Optional[str] = None
    NGROK_ENABLED: bool = False
    NGROK_AUTHTOKEN: Optional[str] = None
    NGROK_DOMAIN: Optional[str] = None

    @field_validator("HF_TOKEN", "CACHE_DIR", "CLOUDFLARE_TUNNEL_TOKEN", "NGROK_AUTHTOKEN", "NGROK_DOMAIN", mode="before")
    @classmethod
    def empty_string_to_none(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        if not self.CORS_ORIGINS or self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [item.strip() for item in self.CORS_ORIGINS.split(",") if item.strip()]

@lru_cache()
def get_settings() -> Settings:
    return Settings()
