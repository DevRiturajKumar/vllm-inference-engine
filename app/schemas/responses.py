from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class UsageInfo(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class ChatMessageResponse(BaseModel):
    role: str = "assistant"
    content: str
    reasoning: Optional[str] = None
    reasoning_content: Optional[str] = None

class ChatChoice(BaseModel):
    index: int = 0
    message: ChatMessageResponse
    finish_reason: Optional[str] = "stop"

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatChoice]
    usage: UsageInfo

class CompletionChoice(BaseModel):
    index: int = 0
    text: str
    finish_reason: Optional[str] = "stop"

class CompletionResponse(BaseModel):
    id: str
    object: str = "text_completion"
    created: int
    model: str
    choices: List[CompletionChoice]
    usage: UsageInfo

class ModelCard(BaseModel):
    id: str
    object: str = "model"
    created: int = 1700000000
    owned_by: str = "vllm"

class ModelListResponse(BaseModel):
    object: str = "list"
    data: List[ModelCard]

class HealthResponse(BaseModel):
    status: str
    loaded_model: Optional[str] = None
    gpu_available: bool = False
    gpu_name: Optional[str] = None
    vram_allocated_gb: Optional[float] = None
    vram_total_gb: Optional[float] = None
    model_weights_gb: Optional[float] = None
    kv_cache_paged_gb: Optional[float] = None
    vram_free_gb: Optional[float] = None
    default_enable_thinking: bool = True
    tunnel_url: Optional[str] = None

class AdminResponse(BaseModel):
    status: str
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
