import pytest
from unittest.mock import patch, MagicMock, mock_open
from app.tunnel import (
    build_cloudflare_tunnel_command,
    build_cloudflare_quick_tunnel_command,
    extract_trycloudflare_url,
    start_cloudflare_quick_tunnel,
    start_cloudflare_tunnel,
    stop_cloudflare_tunnel,
    get_cloudflare_url,
    start_ngrok_tunnel,
    verify_tunnel_config,
    setup_tunnels,
    _cf_state,
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

def test_build_cloudflare_quick_tunnel_command():
    cmd = build_cloudflare_quick_tunnel_command(8006)
    assert cmd == [
        "cloudflared",
        "tunnel",
        "--url",
        "http://127.0.0.1:8006",
        "--no-autoupdate",
    ]

    with pytest.raises(ValueError):
        build_cloudflare_quick_tunnel_command(-1)

    with pytest.raises(ValueError):
        build_cloudflare_quick_tunnel_command(70000)

def test_extract_trycloudflare_url():
    log_text = """
    2026-09-21T10:00:00Z INF Starting tunnel...
    2026-09-21T10:00:00Z INF Requesting tunnel from https://api.trycloudflare.com/tunnel
    2026-09-21T10:00:01Z INF Your quick Tunnel has been created! Visit it at:
    2026-09-21T10:00:01Z INF https://silent-mountain-valley.trycloudflare.com
    2026-09-21T10:00:02Z INF Registered tunnel connection
    """
    url = extract_trycloudflare_url(log_text)
    assert url == "https://silent-mountain-valley.trycloudflare.com"

    # Must NOT consider api.trycloudflare.com
    api_only_log = "2026-09-21T10:00:00Z INF Connecting to https://api.trycloudflare.com/tunnel..."
    assert extract_trycloudflare_url(api_only_log) is None

    assert extract_trycloudflare_url("no url here") is None
    assert extract_trycloudflare_url("") is None

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
        assert cfg["cloudflare_mode"] == "named"
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
         patch("app.tunnel.is_cloudflared_running", return_value=False), \
         patch("subprocess.Popen", return_value=mock_proc):
        proc = start_cloudflare_tunnel("token-abc")
        assert proc is mock_proc

def test_start_cloudflare_quick_tunnel():
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None

    mock_log = "2026-09-21 INF https://test-quick.trycloudflare.com\n"
    with patch("shutil.which", return_value="/usr/bin/cloudflared"), \
         patch("app.tunnel.is_cloudflared_running", return_value=False), \
         patch("subprocess.Popen", return_value=mock_proc), \
         patch("builtins.open", mock_open(read_data=mock_log)):
        proc, url = start_cloudflare_quick_tunnel(8006, timeout=0.5)
        assert proc is mock_proc
        assert url == "https://test-quick.trycloudflare.com"
        assert get_cloudflare_url() == "https://test-quick.trycloudflare.com"

def test_stop_cloudflare_tunnel():
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None
    _cf_state.process = mock_proc
    _cf_state.url = "https://test.trycloudflare.com"

    stop_cloudflare_tunnel()
    mock_proc.terminate.assert_called_once()
    assert _cf_state.process is None
    assert _cf_state.url is None

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

def test_setup_tunnels_quick_tunnel():
    with patch("app.tunnel.start_cloudflare_quick_tunnel", return_value=(MagicMock(), "https://quick.trycloudflare.com")), \
         patch("app.tunnel.get_settings") as mock_settings:
        mock_settings.return_value = Settings(
            CLOUDFLARE_TUNNEL_ENABLED=True,
            CLOUDFLARE_TUNNEL_TOKEN=None,
            NGROK_ENABLED=False
        )
        status = setup_tunnels()
        assert status["cloudflare_started"] is True
        assert status["cloudflare_url"] == "https://quick.trycloudflare.com"

def test_setup_tunnels_disabled():
    with patch("app.tunnel.get_settings") as mock_settings:
        mock_settings.return_value = Settings(
            CLOUDFLARE_TUNNEL_ENABLED=False,
            NGROK_ENABLED=False
        )
        status = setup_tunnels()
        assert status["cloudflare_started"] is False
        assert status["cloudflare_url"] is None
