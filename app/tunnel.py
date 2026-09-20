import os
import re
import shutil
import subprocess
import time
import atexit
from typing import Optional, List, Dict, Any, Tuple
from app.config import get_settings

CLOUDFLARE_URL_REGEX = re.compile(r"https://(?!api\.)[a-zA-Z0-9-]+\.trycloudflare\.com")

class CloudflareTunnelState:
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.url: Optional[str] = None
        self.mode: str = "disabled"

_cf_state = CloudflareTunnelState()

def extract_trycloudflare_url(text: str) -> Optional[str]:
    if not text:
        return None
    for match in CLOUDFLARE_URL_REGEX.finditer(text):
        candidate = match.group(0)
        if not candidate.startswith("https://api.trycloudflare.com"):
            return candidate
    return None

def is_cloudflared_running() -> bool:
    try:
        res = subprocess.run(["pgrep", "-f", "cloudflared tunnel"], capture_output=True)
        return res.returncode == 0
    except Exception:
        return False

def build_cloudflare_tunnel_command(token: str) -> List[str]:
    if not token or not token.strip():
        raise ValueError("Cloudflare tunnel token cannot be empty")
    return ["cloudflared", "tunnel", "run", "--token", token.strip()]

def build_cloudflare_quick_tunnel_command(port: int, host: str = "127.0.0.1") -> List[str]:
    if not isinstance(port, int) or port < 1 or port > 65535:
        raise ValueError(f"Invalid port: {port}")
    return [
        "cloudflared",
        "tunnel",
        "--url",
        f"http://{host}:{port}",
        "--no-autoupdate",
    ]

def start_cloudflare_quick_tunnel(
    port: int,
    host: str = "127.0.0.1",
    log_path: str = "cloudflared.log",
    timeout: float = 25.0,
) -> Tuple[Optional[subprocess.Popen], Optional[str]]:
    global _cf_state
    if not shutil.which("cloudflared"):
        return None, None

    if is_cloudflared_running():
        # Stop unmanaged stale instance so a fresh quick tunnel URL is bound
        subprocess.run(["pkill", "-f", "cloudflared tunnel"], capture_output=True)
        time.sleep(0.5)

    cmd = build_cloudflare_quick_tunnel_command(port=port, host=host)
    try:
        log_file = open(log_path, "w+", encoding="utf-8")
        proc = subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    except Exception:
        return None, None

    url: Optional[str] = None
    start_time = time.time()

    try:
        with open(log_path, "r", encoding="utf-8") as rf:
            while time.time() - start_time < timeout:
                if proc.poll() is not None:
                    break
                line = rf.readline()
                if line:
                    found = extract_trycloudflare_url(line)
                    if found:
                        url = found
                        break
                else:
                    time.sleep(0.2)
    except Exception:
        pass

    _cf_state.process = proc
    _cf_state.url = url
    _cf_state.mode = "quick"

    if url:
        try:
            with open("tunnel_url.txt", "w", encoding="utf-8") as f:
                f.write(f"{url}\n")
        except Exception:
            pass

    return proc, url

def start_cloudflare_tunnel(token: Optional[str] = None) -> Optional[subprocess.Popen]:
    global _cf_state
    settings = get_settings()
    active_token = token or settings.CLOUDFLARE_TUNNEL_TOKEN
    if not active_token:
        return None

    if is_cloudflared_running():
        return None

    cloudflared_bin = shutil.which("cloudflared")
    if not cloudflared_bin:
        return None

    cmd = build_cloudflare_tunnel_command(active_token)
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    _cf_state.process = proc
    _cf_state.mode = "named"
    return proc

def stop_cloudflare_tunnel() -> None:
    global _cf_state
    proc = _cf_state.process
    if proc is not None:
        try:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=3.0)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=1.0)
        except Exception:
            pass
        _cf_state.process = None
        _cf_state.url = None
        _cf_state.mode = "disabled"

atexit.register(stop_cloudflare_tunnel)

def get_cloudflare_url() -> Optional[str]:
    return _cf_state.url

def start_ngrok_tunnel(
    port: int,
    authtoken: Optional[str] = None,
    domain: Optional[str] = None
) -> Optional[str]:
    settings = get_settings()
    token = authtoken or settings.NGROK_AUTHTOKEN
    if not token:
        return None
    try:
        from pyngrok import ngrok
        ngrok.set_auth_token(token)
        kwargs: Dict[str, Any] = {"addr": port}
        dom = domain or settings.NGROK_DOMAIN
        if dom:
            kwargs["domain"] = dom
        tunnel = ngrok.connect(**kwargs)
        return tunnel.public_url
    except Exception:
        return None

def verify_tunnel_config() -> Dict[str, Any]:
    settings = get_settings()
    return {
        "cloudflare_enabled": bool(settings.CLOUDFLARE_TUNNEL_ENABLED),
        "cloudflare_token_present": bool(settings.CLOUDFLARE_TUNNEL_TOKEN),
        "cloudflare_mode": "named" if settings.CLOUDFLARE_TUNNEL_TOKEN else "quick",
        "ngrok_enabled": bool(settings.NGROK_ENABLED and settings.NGROK_AUTHTOKEN),
        "ngrok_authtoken_present": bool(settings.NGROK_AUTHTOKEN),
        "ngrok_domain": settings.NGROK_DOMAIN,
    }

def setup_tunnels() -> Dict[str, Any]:
    settings = get_settings()
    status_info: Dict[str, Any] = {
        "cloudflare_started": False,
        "cloudflare_url": None,
        "ngrok_url": None,
    }

    if settings.CLOUDFLARE_TUNNEL_ENABLED:
        if settings.CLOUDFLARE_TUNNEL_TOKEN:
            # Token-based Named Tunnel
            if is_cloudflared_running():
                status_info["cloudflare_started"] = True
            else:
                proc = start_cloudflare_tunnel(settings.CLOUDFLARE_TUNNEL_TOKEN)
                status_info["cloudflare_started"] = proc is not None
        else:
            # Ephemeral Quick Tunnel via trycloudflare.com
            proc, url = start_cloudflare_quick_tunnel(port=settings.PORT)
            status_info["cloudflare_started"] = proc is not None
            status_info["cloudflare_url"] = url

    if settings.NGROK_ENABLED and settings.NGROK_AUTHTOKEN:
        url = start_ngrok_tunnel(
            port=settings.PORT,
            authtoken=settings.NGROK_AUTHTOKEN,
            domain=settings.NGROK_DOMAIN,
        )
        status_info["ngrok_url"] = url

    return status_info
