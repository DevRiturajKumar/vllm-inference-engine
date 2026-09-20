from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: Optional[str] = None
    messages: List[ChatMessage]
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    repetition_penalty: Optional[float] = None
    stop: Optional[Union[str, List[str]]] = None
    stream: bool = False
    do_sample: Optional[bool] = None
    enable_thinking: Optional[bool] = None
    thinking: Optional[Union[bool, Dict[str, Any]]] = None
    thinking_budget: Optional[int] = None

    def resolved_enable_thinking(self) -> Optional[bool]:
        if self.enable_thinking is not None:
            return self.enable_thinking
        if self.thinking is not None:
            if isinstance(self.thinking, bool):
                return self.thinking
            if isinstance(self.thinking, dict):
                val = self.thinking.get("type")
                if val in ("enabled", "true", True):
                    return True
                if val in ("disabled", "false", False):
                    return False
        return None

class CompletionRequest(BaseModel):
    model: Optional[str] = None
    prompt: Union[str, List[str]]
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    repetition_penalty: Optional[float] = None
    stop: Optional[Union[str, List[str]]] = None
    stream: bool = False
    do_sample: Optional[bool] = None

class LoadModelRequest(BaseModel):
    model_id: str
    quantization: Optional[str] = None
    max_model_len: Optional[int] = None
    gpu_memory_utilization: Optional[float] = None
    enforce_eager: Optional[bool] = None
    hf_token: Optional[str] = None
