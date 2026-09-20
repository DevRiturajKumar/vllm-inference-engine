import os
import shutil
import subprocess
from typing import Optional, List, Dict, Any
from app.config import get_settings

def build_cloudflare_tunnel_command(token: str) -> List[str]:
    if not token or not token.strip():
        raise ValueError("Cloudflare tunnel token cannot be empty")
    return ["cloudflared", "tunnel", "run", "--token", token.strip()]

def start_cloudflare_tunnel(token: Optional[str] = None) -> Optional[subprocess.Popen]:
    settings = get_settings()
    active_token = token or settings.CLOUDFLARE_TUNNEL_TOKEN
    if not active_token:
        return None
    
    cmd = build_cloudflare_tunnel_command(active_token)
    cloudflared_bin = shutil.which("cloudflared")
    if not cloudflared_bin:
        return None
    
    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True
    )

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
        "cloudflare_enabled": bool(settings.CLOUDFLARE_TUNNEL_ENABLED and settings.CLOUDFLARE_TUNNEL_TOKEN),
        "cloudflare_token_present": bool(settings.CLOUDFLARE_TUNNEL_TOKEN),
        "ngrok_enabled": bool(settings.NGROK_ENABLED and settings.NGROK_AUTHTOKEN),
        "ngrok_authtoken_present": bool(settings.NGROK_AUTHTOKEN),
        "ngrok_domain": settings.NGROK_DOMAIN,
    }

def setup_tunnels() -> Dict[str, Any]:
    settings = get_settings()
    status_info: Dict[str, Any] = {
        "cloudflare_started": False,
        "ngrok_url": None,
    }
    if settings.CLOUDFLARE_TUNNEL_ENABLED and settings.CLOUDFLARE_TUNNEL_TOKEN:
        proc = start_cloudflare_tunnel(settings.CLOUDFLARE_TUNNEL_TOKEN)
        status_info["cloudflare_started"] = proc is not None

    if settings.NGROK_ENABLED and settings.NGROK_AUTHTOKEN:
        url = start_ngrok_tunnel(
            port=settings.PORT,
            authtoken=settings.NGROK_AUTHTOKEN,
            domain=settings.NGROK_DOMAIN
        )
        status_info["ngrok_url"] = url

    return status_info
