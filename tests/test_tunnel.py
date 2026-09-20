import pytest
from unittest.mock import patch, MagicMock
from app.tunnel import (
    build_cloudflare_tunnel_command,
    start_cloudflare_tunnel,
    start_ngrok_tunnel,
    verify_tunnel_config,
    setup_tunnels,
)
from app.config import Settings, get_settings

def test_build_cloudflare_tunnel_command_valid():
    cmd = build_cloudflare_tunnel_command("test-token-123")
    assert cmd == ["cloudflared", "tunnel", "run", "--token", "test-token-123"]

def test_build_cloudflare_tunnel_command_invalid():
    with pytest.raises(ValueError):
        build_cloudflare_tunnel_command("")

    with pytest.raises(ValueError):
        build_cloudflare_tunnel_command("   ")

def test_verify_tunnel_config(monkeypatch):
    monkeypatch.setenv("CLOUDFLARE_TUNNEL_ENABLED", "true")
    monkeypatch.setenv("CLOUDFLARE_TUNNEL_TOKEN", "mock-token")
    monkeypatch.setenv("NGROK_ENABLED", "true")
    monkeypatch.setenv("NGROK_AUTHTOKEN", "mock-ngrok")
    monkeypatch.setenv("NGROK_DOMAIN", "foo.ngrok-free.app")

    get_settings.cache_clear()
    try:
        cfg = verify_tunnel_config()
        assert cfg["cloudflare_enabled"] is True
        assert cfg["cloudflare_token_present"] is True
        assert cfg["ngrok_enabled"] is True
        assert cfg["ngrok_authtoken_present"] is True
        assert cfg["ngrok_domain"] == "foo.ngrok-free.app"
    finally:
        get_settings.cache_clear()

def test_start_cloudflare_tunnel_no_binary():
    with patch("shutil.which", return_value=None):
        proc = start_cloudflare_tunnel("token-abc")
        assert proc is None

def test_start_cloudflare_tunnel_with_binary():
    mock_proc = MagicMock()
    with patch("shutil.which", return_value="/usr/local/bin/cloudflared"), \
         patch("subprocess.Popen", return_value=mock_proc):
        proc = start_cloudflare_tunnel("token-abc")
        assert proc is mock_proc

def test_start_ngrok_tunnel_no_token():
    res = start_ngrok_tunnel(8006, authtoken=None)
    assert res is None

def test_setup_tunnels():
    with patch("app.tunnel.start_cloudflare_tunnel", return_value=MagicMock()), \
         patch("app.tunnel.start_ngrok_tunnel", return_value="https://test.ngrok.app"), \
         patch("app.tunnel.get_settings") as mock_settings:
        mock_settings.return_value = Settings(
            CLOUDFLARE_TUNNEL_ENABLED=True,
            CLOUDFLARE_TUNNEL_TOKEN="token123",
            NGROK_ENABLED=True,
            NGROK_AUTHTOKEN="ngrok123"
        )
        status = setup_tunnels()
        assert status["cloudflare_started"] is True
        assert status["ngrok_url"] == "https://test.ngrok.app"
