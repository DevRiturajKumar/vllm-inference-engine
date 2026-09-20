import json
import uuid
import time
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse
from app.config import get_settings
from app.engine import get_vllm_manager
from app.schemas.requests import ChatCompletionRequest
from app.thinking import (
    is_thinking_model,
    parse_thinking_content,
    StreamingThinkingParser,
)

router = APIRouter(tags=["Inference"])

def normalize_messages_for_template(messages: list) -> list:
    if not messages:
        return messages
    merged = []
    system_content = ""
    for m in messages:
        if m.get("role") == "system":
            system_content += m.get("content", "") + "\n\n"
        elif m.get("role") == "user":
            if system_content:
                merged.append({"role": "user", "content": system_content + m.get("content", "")})
                system_content = ""
            else:
                merged.append(m)
        else:
            merged.append(m)
    if system_content:
        merged.append({"role": "user", "content": system_content.strip()})
    return merged

@router.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest):
    vm = get_vllm_manager()
    if not vm.is_loaded():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No model is currently loaded in the vLLM engine.",
            headers={"Retry-After": "5"}
        )

    settings = get_settings()
    req_thinking = req.resolved_enable_thinking()
    if req_thinking is not None:
        enable_thinking = req_thinking
    else:
        enable_thinking = is_thinking_model(vm.model_id) or settings.DEFAULT_ENABLE_THINKING

    req_data = req.model_dump()
    req_id = f"chatcmpl-{uuid.uuid4()}"
    created_ts = int(time.time())

    # Protect against multi-turn transcript hallucination
    chat_stops = ["\nuser:", "\nUser:", "\n[INST]"]
    if req_data.get("stop"):
        existing_stops = [req_data["stop"]] if isinstance(req_data["stop"], str) else list(req_data["stop"])
        for s in chat_stops:
            if s not in existing_stops:
                existing_stops.append(s)
        req_data["stop"] = existing_stops
    else:
        req_data["stop"] = chat_stops

    sampling_params = vm.build_sampling_params(req_data)

    messages = [{"role": m.role, "content": m.content} for m in req.messages]
    prompt = None

    if hasattr(vm.tokenizer, "apply_chat_template") and callable(vm.tokenizer.apply_chat_template):
        # 1. Try with enable_thinking
        try:
            prompt = vm.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=enable_thinking,
            )
        except (TypeError, Exception):
            pass

        # 2. Try standard apply_chat_template
        if prompt is None:
            try:
                prompt = vm.tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True,
                )
            except Exception:
                pass

        # 3. Try with normalized/merged system message (for Mistral and Gemma models that reject system role)
        if prompt is None:
            try:
                merged_msgs = normalize_messages_for_template(messages)
                prompt = vm.tokenizer.apply_chat_template(
                    merged_msgs,
                    tokenize=False,
                    add_generation_prompt=True,
                )
            except Exception:
                pass

    if prompt is None:
        prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages) + "\nassistant:"

    prompt_has_thinking_open = bool(
        prompt.rstrip().endswith("<think>") or prompt.rstrip().endswith("<thinking>")
    )

    if req.stream:
        async def stream_generator():
            try:
                results_generator = vm.engine.generate(prompt, sampling_params, req_id)
                stream_parser = StreamingThinkingParser(
                    enable_thinking=enable_thinking,
                    prompt_has_thinking_open=prompt_has_thinking_open,
                )

                yield f"data: {json.dumps({'id': req_id, 'object': 'chat.completion.chunk', 'created': created_ts, 'model': vm.model_id, 'choices': [{'index': 0, 'delta': {'role': 'assistant', 'content': ''}, 'finish_reason': None}]})}\n\n"

                async for request_output in results_generator:
                    current_text = request_output.outputs[0].text
                    events = stream_parser.process(current_text)

                    for ev in events:
                        delta_payload = {}
                        if "reasoning" in ev:
                            delta_payload["reasoning"] = ev["reasoning"]
                            delta_payload["reasoning_content"] = ev["reasoning"]
                        if "content" in ev:
                            delta_payload["content"] = ev["content"]

                        chunk = {
                            "id": req_id,
                            "object": "chat.completion.chunk",
                            "created": created_ts,
                            "model": vm.model_id,
                            "choices": [{
                                "index": 0,
                                "delta": delta_payload,
                                "finish_reason": None,
                            }]
                        }
                        yield f"data: {json.dumps(chunk)}\n\n"

                yield f"data: {json.dumps({'id': req_id, 'object': 'chat.completion.chunk', 'created': created_ts, 'model': vm.model_id, 'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'stop'}]})}\n\n"
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

    results_generator = vm.engine.generate(prompt, sampling_params, req_id)
    final_output = None
    async for output in results_generator:
        final_output = output

    generated_text = final_output.outputs[0].text if final_output and final_output.outputs else ""
    prompt_tokens = len(final_output.prompt_token_ids) if final_output and hasattr(final_output, "prompt_token_ids") and final_output.prompt_token_ids else 0
    completion_tokens = len(final_output.outputs[0].token_ids) if final_output and final_output.outputs and hasattr(final_output.outputs[0], "token_ids") and final_output.outputs[0].token_ids else len(generated_text.split())
    finish_reason = final_output.outputs[0].finish_reason if final_output and final_output.outputs and hasattr(final_output.outputs[0], "finish_reason") else "stop"

    raw_reasoning, parsed_content = parse_thinking_content(generated_text)
    if not enable_thinking:
        reasoning_val = None
        final_content = parsed_content
    else:
        if prompt_has_thinking_open and ("</think>" in generated_text or "</thinking>" in generated_text):
            raw_reasoning, final_content = parse_thinking_content("<think>" + generated_text)
        elif prompt_has_thinking_open and "<think>" not in generated_text and "<thinking>" not in generated_text:
            raw_reasoning = generated_text.strip()
            final_content = ""
        else:
            raw_reasoning, final_content = raw_reasoning, parsed_content
        reasoning_val = raw_reasoning

    msg_dict = {
        "role": "assistant",
        "content": final_content,
    }
    if reasoning_val is not None:
        msg_dict["reasoning"] = reasoning_val
        msg_dict["reasoning_content"] = reasoning_val

    return JSONResponse(content={
        "id": req_id,
        "object": "chat.completion",
        "created": created_ts,
        "model": vm.model_id,
        "choices": [
            {
                "index": 0,
                "message": msg_dict,
                "finish_reason": finish_reason or "stop",
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        }
    })
