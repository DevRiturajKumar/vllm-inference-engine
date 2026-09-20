from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.config import get_settings
from app.engine import get_vllm_manager
from app.tunnel import setup_tunnels
from app.routes import chat, completions, models, health, admin

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    vm = get_vllm_manager()
    if settings.AUTO_LOAD_ON_STARTUP:
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
        setup_tunnels()
    except Exception:
        pass
    yield
    if vm.is_loaded():
        await vm.unload_model()

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="vLLM Inference Engine",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

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

    @app.get("/")
    async def root():
        return {"service": "vllm-inference-engine", "status": "running"}

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
