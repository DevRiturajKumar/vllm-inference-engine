import os
import pytest
from app.config import Settings, get_settings

def test_default_config_values():
    settings = Settings(_env_file=None)
    assert settings.HOST == "0.0.0.0"
    assert settings.PORT == 8006
    assert settings.LOG_LEVEL == "info"
    assert settings.MODEL_ID == "Qwen/Qwen2.5-1.5B-Instruct"
    assert settings.MODEL_REVISION == "main"
    assert settings.QUANTIZATION == "none"
    assert settings.DTYPE == "auto"
    assert settings.MAX_MODEL_LEN == 4096
    assert settings.GPU_MEMORY_UTILIZATION == 0.85
    assert settings.ENFORCE_EAGER is True
    assert settings.TENSOR_PARALLEL_SIZE == 1
    assert settings.TRUST_REMOTE_CODE is True
    assert settings.HF_TOKEN is None
    assert settings.CACHE_DIR is None
    assert settings.DEFAULT_ENABLE_THINKING is True

def test_cors_parsing():
    s1 = Settings(CORS_ORIGINS="*")
    assert s1.cors_origins_list == ["*"]

    s2 = Settings(CORS_ORIGINS="https://foo.com, https://bar.com")
    assert s2.cors_origins_list == ["https://foo.com", "https://bar.com"]

    s3 = Settings(CORS_ORIGINS="")
    assert s3.cors_origins_list == ["*"]

def test_type_casting():
    s = Settings(
        PORT="9000",
        GPU_MEMORY_UTILIZATION="0.75",
        ENFORCE_EAGER="false",
        DEFAULT_MAX_TOKENS="256",
        DEFAULT_TEMPERATURE="0.5"
    )
    assert s.PORT == 9000
    assert s.GPU_MEMORY_UTILIZATION == 0.75
    assert s.ENFORCE_EAGER is False
    assert s.DEFAULT_MAX_TOKENS == 256
    assert s.DEFAULT_TEMPERATURE == 0.5

def test_env_overrides(monkeypatch):
    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv("PORT", "7777")
    monkeypatch.setenv("MODEL_ID", "custom/test-model")
    s = Settings()
    assert s.HOST == "127.0.0.1"
    assert s.PORT == 7777
    assert s.MODEL_ID == "custom/test-model"

def test_fallback_toggle_defaults():
    s = Settings()
    assert s.ENABLE_FALLBACK_TRANSFORMERS_BACKEND is True
    assert s.ENABLE_PREFIX_CACHING is True
    assert s.ALLOW_CPU_FALLBACK is False
    assert s.AUTO_LOAD_ON_STARTUP is True

def test_get_settings_cached():
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
