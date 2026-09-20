import json
import uuid
import time
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse
from app.engine import get_vllm_manager
from app.schemas.requests import CompletionRequest

router = APIRouter(tags=["Inference"])

@router.post("/v1/completions")
async def completions(req: CompletionRequest):
    vm = get_vllm_manager()
    if not vm.is_loaded():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No model is currently loaded in the vLLM engine.",
            headers={"Retry-After": "5"}
        )

    req_data = req.model_dump()
    req_id = f"cmpl-{uuid.uuid4()}"
    created_ts = int(time.time())
    sampling_params = vm.build_sampling_params(req_data)

    prompts = [req.prompt] if isinstance(req.prompt, str) else req.prompt

    if req.stream:
        async def stream_generator():
            try:
                for idx, prompt in enumerate(prompts):
                    p_req_id = f"{req_id}-{idx}"
                    results_generator = vm.engine.generate(prompt, sampling_params, p_req_id)
                    previous_text = ""

                    async for request_output in results_generator:
                        current_text = request_output.outputs[0].text
                        delta_text = current_text[len(previous_text):]
                        previous_text = current_text

                        if delta_text:
                            chunk = {
                                "id": req_id,
                                "object": "text_completion",
                                "created": created_ts,
                                "model": vm.model_id,
                                "choices": [{
                                    "index": idx,
                                    "text": delta_text,
                                    "finish_reason": None,
                                }]
                            }
                            yield f"data: {json.dumps(chunk)}\n\n"

                    final_chunk = {
                        "id": req_id,
                        "object": "text_completion",
                        "created": created_ts,
                        "model": vm.model_id,
                        "choices": [{
                            "index": idx,
                            "text": "",
                            "finish_reason": "stop",
                        }]
                    }
                    yield f"data: {json.dumps(final_chunk)}\n\n"

                yield "data: [DONE]\n\n"
            except Exception as e:
                err_chunk = {"error": {"message": str(e), "type": type(e).__name__}}
                yield f"data: {json.dumps(err_chunk)}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
        )

    choices = []
    total_prompt_tokens = 0
    total_completion_tokens = 0

    for idx, prompt in enumerate(prompts):
        p_req_id = f"{req_id}-{idx}"
        results_generator = vm.engine.generate(prompt, sampling_params, p_req_id)
        final_output = None
        async for output in results_generator:
            final_output = output

        generated_text = final_output.outputs[0].text if final_output and final_output.outputs else ""
        prompt_tokens = len(final_output.prompt_token_ids) if final_output and hasattr(final_output, "prompt_token_ids") and final_output.prompt_token_ids else 0
        completion_tokens = len(final_output.outputs[0].token_ids) if final_output and final_output.outputs and hasattr(final_output.outputs[0], "token_ids") and final_output.outputs[0].token_ids else len(generated_text.split())
        finish_reason = final_output.outputs[0].finish_reason if final_output and final_output.outputs and hasattr(final_output.outputs[0], "finish_reason") else "stop"

        total_prompt_tokens += prompt_tokens
        total_completion_tokens += completion_tokens

        choices.append({
            "index": idx,
            "text": generated_text,
            "finish_reason": finish_reason or "stop",
        })

    return JSONResponse(content={
        "id": req_id,
        "object": "text_completion",
        "created": created_ts,
        "model": vm.model_id,
        "choices": choices,
        "usage": {
            "prompt_tokens": total_prompt_tokens,
            "completion_tokens": total_completion_tokens,
            "total_tokens": total_prompt_tokens + total_completion_tokens,
        }
    })
