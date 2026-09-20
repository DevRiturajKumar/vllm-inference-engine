import torch
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.engine import get_vllm_manager

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health():
    vm = get_vllm_manager()
    gpu_available = torch.cuda.is_available()
    gpu_name = None
    vram_allocated = None
    vram_total = None

    if gpu_available:
        try:
            gpu_name = torch.cuda.get_device_name(0)
            vram_allocated = round(torch.cuda.memory_allocated(0) / (1024 ** 3), 2)
            total_mem = torch.cuda.get_device_properties(0).total_memory
            vram_total = round(total_mem / (1024 ** 3), 2)
        except Exception:
            pass

    if vm.is_loaded():
        status_text = "OK"
        loaded_model = vm.model_id
    else:
        status_text = "READY_NO_MODEL"
        loaded_model = None

    return JSONResponse(content={
        "status": status_text,
        "loaded_model": loaded_model,
        "gpu_available": gpu_available,
        "gpu_name": gpu_name,
        "vram_allocated_gb": vram_allocated,
        "vram_total_gb": vram_total,
    })
