import pytest
from app.config import Settings

def test_fallback_defaults():
    s = Settings()
    assert s.ENABLE_FALLBACK_TRANSFORMERS_BACKEND is True
    assert s.ENABLE_PREFIX_CACHING is True
    assert s.ALLOW_CPU_FALLBACK is False
    assert s.AUTO_LOAD_ON_STARTUP is False

def test_fallback_env_overrides(monkeypatch):
    monkeypatch.setenv("ENABLE_FALLBACK_TRANSFORMERS_BACKEND", "false")
    monkeypatch.setenv("ENABLE_PREFIX_CACHING", "false")
    monkeypatch.setenv("ALLOW_CPU_FALLBACK", "true")
    monkeypatch.setenv("AUTO_LOAD_ON_STARTUP", "true")

    s = Settings()
    assert s.ENABLE_FALLBACK_TRANSFORMERS_BACKEND is False
    assert s.ENABLE_PREFIX_CACHING is False
    assert s.ALLOW_CPU_FALLBACK is True
    assert s.AUTO_LOAD_ON_STARTUP is True

def test_fallback_truthy_falsy_parsing():
    s_truthy = Settings(
        ENABLE_FALLBACK_TRANSFORMERS_BACKEND="1",
        ENABLE_PREFIX_CACHING="yes",
        ALLOW_CPU_FALLBACK="True"
    )
    assert s_truthy.ENABLE_FALLBACK_TRANSFORMERS_BACKEND is True
    assert s_truthy.ENABLE_PREFIX_CACHING is True
    assert s_truthy.ALLOW_CPU_FALLBACK is True

    s_falsy = Settings(
        ENABLE_FALLBACK_TRANSFORMERS_BACKEND="0",
        ENABLE_PREFIX_CACHING="no",
        ALLOW_CPU_FALLBACK="false"
    )
    assert s_falsy.ENABLE_FALLBACK_TRANSFORMERS_BACKEND is False
    assert s_falsy.ENABLE_PREFIX_CACHING is False
    assert s_falsy.ALLOW_CPU_FALLBACK is False
