import torch
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.engine import get_vllm_manager
from app.tunnel import get_cloudflare_url

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
            total_mem = torch.cuda.get_device_properties(0).total_memory
            vram_total = round(total_mem / (1024 ** 3), 2)

            # 1. Device-wide hardware query (NVML / CUDA driver)
            # captures vLLM child worker processes and paged KV cache
            real_used = None
            if hasattr(torch.cuda, "mem_get_info"):
                try:
                    free_b, total_b = torch.cuda.mem_get_info(0)
                    used_b = total_b - free_b
                    if used_b > 0:
                        real_used = round(used_b / (1024 ** 3), 2)
                except Exception:
                    pass

            # 2. PyTorch current process allocation
            process_allocated = round(torch.cuda.memory_allocated(0) / (1024 ** 3), 2)

            if real_used is not None and real_used > 0:
                vram_allocated = real_used
            elif process_allocated > 0:
                vram_allocated = process_allocated
            elif vm.is_loaded() and vram_total:
                # vLLM pre-allocates weights & KV cache based on gpu_memory_utilization
                util = vm.active_config.get("gpu_memory_utilization", 0.85) if vm.active_config else 0.85
                vram_allocated = round(vram_total * float(util), 2)
            else:
                vram_allocated = process_allocated
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
        "tunnel_url": get_cloudflare_url(),
    })
