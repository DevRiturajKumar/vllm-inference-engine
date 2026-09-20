from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn
from app.config import get_settings
from app.engine import get_vllm_manager
from app.tunnel import setup_tunnels, stop_cloudflare_tunnel, get_cloudflare_url
from app.routes import chat, completions, models, health, admin

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    vm = get_vllm_manager()
    app.state.tunnel_url = None

    if settings.AUTO_LOAD_ON_STARTUP and settings.MODEL_ID:
        try:
            await vm.load_model(
                model_id=settings.MODEL_ID,
                quantization=settings.QUANTIZATION,
                max_model_len=settings.MAX_MODEL_LEN,
                gpu_memory_utilization=settings.GPU_MEMORY_UTILIZATION,
                enforce_eager=settings.ENFORCE_EAGER,
                hf_token=settings.HF_TOKEN,
            )
        except Exception:
            pass

    try:
        tunnel_info = setup_tunnels()
        app.state.tunnel_url = tunnel_info.get("cloudflare_url")
        if app.state.tunnel_url:
            print("\n" + "=" * 66)
            print(" 🚀 vLLM Inference Engine Online!")
            print(f" 🌐 Cloudflare Quick Tunnel: {app.state.tunnel_url}")
            print(f" 📚 Swagger Documentation:   {app.state.tunnel_url}/docs")
            print(f" 💻 Local Address:           http://localhost:{settings.PORT}")
            print("=" * 66 + "\n")
        elif settings.CLOUDFLARE_TUNNEL_ENABLED and settings.CLOUDFLARE_TUNNEL_TOKEN:
            print(f"\n[Tunnel] Cloudflare Named Tunnel active on port {settings.PORT}.\n")
        else:
            print(f"\n[Server] Localhost mode active on port {settings.PORT} (Tunnel disabled).\n")
    except Exception:
        pass

    yield

    if vm.is_loaded():
        await vm.unload_model()
    try:
        stop_cloudflare_tunnel()
    except Exception:
        pass

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="vLLM Inference Engine",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(SecurityHeadersMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(chat.router)
    app.include_router(completions.router)
    app.include_router(models.router)
    app.include_router(health.router)
    app.include_router(admin.router)

    # Convenience alias in case client appends /docs to base URL
    @app.get("/docs/health", include_in_schema=False)
    async def docs_health():
        return await health.health()

    @app.get("/")
    async def root(request: Request):
        tunnel_url = getattr(request.app.state, "tunnel_url", None) or get_cloudflare_url()
        return {
            "service": "vllm-inference-engine",
            "status": "running",
            "docs": "/docs",
            "tunnel_url": tunnel_url,
        }

    return app

app = create_app()

if __name__ == "__main__":
    current_settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=current_settings.HOST,
        port=current_settings.PORT,
        log_level=current_settings.LOG_LEVEL,
    )
