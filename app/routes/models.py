import time
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.engine import get_vllm_manager

router = APIRouter(tags=["Models"])

@router.get("/v1/models")
async def list_models():
    vm = get_vllm_manager()
    if not vm.is_loaded():
        return JSONResponse(content={"object": "list", "data": []})

    model_card = {
        "id": vm.model_id,
        "object": "model",
        "created": int(time.time()),
        "owned_by": "vllm",
    }
    return JSONResponse(content={"object": "list", "data": [model_card]})
