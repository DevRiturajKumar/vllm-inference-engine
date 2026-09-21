import re
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import JSONResponse
from app.engine import get_vllm_manager
from app.schemas.requests import LoadModelRequest

router = APIRouter(prefix="/admin", tags=["Admin"])

def sanitize_error_detail(err: Exception) -> str:
    msg = str(err)
    # Redact sensitive bearer or Hugging Face tokens
    msg = re.sub(r"hf_[a-zA-Z0-9]{10,}", "hf_***REDACTED***", msg)
    msg = re.sub(r"Bearer\s+[a-zA-Z0-9_\-\.]{10,}", "Bearer ***REDACTED***", msg)
    return msg

@router.post("/load-model")
async def load_model(req: LoadModelRequest):
    vm = get_vllm_manager()
    try:
        details = await vm.load_model(
            model_id=req.model_id,
            quantization=req.quantization,
            max_model_len=req.max_model_len,
            gpu_memory_utilization=req.gpu_memory_utilization,
            enforce_eager=req.enforce_eager,
            hf_token=req.hf_token,
            dtype=req.dtype,
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "LOADED", "details": details}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=sanitize_error_detail(e)
        )

@router.get("/switch-model/{model_id:path}")
async def switch_model_get(
    model_id: str,
    quantization: Optional[str] = Query(None),
    dtype: Optional[str] = Query(None),
    max_model_len: Optional[int] = Query(None),
    gpu_memory_utilization: Optional[float] = Query(None),
    enforce_eager: Optional[bool] = Query(None),
    hf_token: Optional[str] = Query(None),
):
    clean_id = model_id.strip() if model_id else ""
    if not clean_id or ".." in clean_id or clean_id.startswith(("/etc", "/root", "/var", "/bin", "/sbin", "/proc", "/sys", "/dev")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path traversal or restricted system path detected in model_id"
        )

    if gpu_memory_utilization is not None and not (0.0 < gpu_memory_utilization <= 1.0):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="gpu_memory_utilization must be between 0.0 and 1.0"
        )

    vm = get_vllm_manager()
    try:
        details = await vm.load_model(
            model_id=clean_id,
            quantization=quantization,
            max_model_len=max_model_len,
            gpu_memory_utilization=gpu_memory_utilization,
            enforce_eager=enforce_eager,
            hf_token=hf_token,
            dtype=dtype,
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "LOADED", "details": details}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=sanitize_error_detail(e)
        )

@router.get("/current-model")
async def current_model():
    vm = get_vllm_manager()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "is_loaded": vm.is_loaded(),
            "model_id": vm.model_id,
            "active_config": vm.active_config,
        }
    )

@router.post("/unload-model")
@router.get("/unload-model")
async def unload_model():
    vm = get_vllm_manager()
    try:
        details = await vm.unload_model()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "UNLOADED", "details": details}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=sanitize_error_detail(e)
        )
