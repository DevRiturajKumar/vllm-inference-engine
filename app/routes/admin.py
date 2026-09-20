from typing import Optional
from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import JSONResponse
from app.engine import get_vllm_manager
from app.schemas.requests import LoadModelRequest

router = APIRouter(prefix="/admin", tags=["Admin"])

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
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "LOADED", "details": details}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/switch-model/{model_id:path}")
async def switch_model_get(
    model_id: str,
    quantization: Optional[str] = Query(None),
    max_model_len: Optional[int] = Query(None),
    gpu_memory_utilization: Optional[float] = Query(None),
    enforce_eager: Optional[bool] = Query(None),
    hf_token: Optional[str] = Query(None),
):
    vm = get_vllm_manager()
    try:
        details = await vm.load_model(
            model_id=model_id,
            quantization=quantization,
            max_model_len=max_model_len,
            gpu_memory_utilization=gpu_memory_utilization,
            enforce_eager=enforce_eager,
            hf_token=hf_token,
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "LOADED", "details": details}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
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
            detail=str(e)
        )
