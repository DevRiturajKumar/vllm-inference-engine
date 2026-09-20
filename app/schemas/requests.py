import math
import re
from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field, field_validator

class ChatMessage(BaseModel):
    role: str
    content: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Role cannot be empty")
        return v.strip().lower()

class ChatCompletionRequest(BaseModel):
    model: Optional[str] = None
    messages: List[ChatMessage] = Field(..., min_length=1)
    max_tokens: Optional[int] = Field(None, ge=1, le=65536)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(None, gt=0.0, le=1.0)
    top_k: Optional[int] = Field(None, ge=-1, le=1000)
    repetition_penalty: Optional[float] = Field(None, gt=0.0, le=2.0)
    stop: Optional[Union[str, List[str]]] = None
    stream: bool = False
    do_sample: Optional[bool] = None
    enable_thinking: Optional[bool] = None
    thinking: Optional[Union[bool, Dict[str, Any]]] = None
    thinking_budget: Optional[int] = None

    @field_validator("temperature", "top_p", "repetition_penalty")
    @classmethod
    def validate_floats(cls, v):
        if v is not None:
            if math.isnan(v) or math.isinf(v):
                raise ValueError("Float parameters must be finite numbers")
        return v

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
    max_tokens: Optional[int] = Field(None, ge=1, le=65536)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(None, gt=0.0, le=1.0)
    top_k: Optional[int] = Field(None, ge=-1, le=1000)
    repetition_penalty: Optional[float] = Field(None, gt=0.0, le=2.0)
    stop: Optional[Union[str, List[str]]] = None
    stream: bool = False
    do_sample: Optional[bool] = None

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, v: Union[str, List[str]]) -> Union[str, List[str]]:
        if isinstance(v, list):
            if len(v) == 0:
                raise ValueError("Prompt list cannot be empty")
            if len(v) > 256:
                raise ValueError("Batch prompt exceeds maximum size of 256")
        elif isinstance(v, str):
            if not v:
                raise ValueError("Prompt string cannot be empty")
        return v

    @field_validator("temperature", "top_p", "repetition_penalty")
    @classmethod
    def validate_floats(cls, v):
        if v is not None:
            if math.isnan(v) or math.isinf(v):
                raise ValueError("Float parameters must be finite numbers")
        return v

class LoadModelRequest(BaseModel):
    model_id: str
    quantization: Optional[str] = None
    max_model_len: Optional[int] = Field(None, ge=1, le=131072)
    gpu_memory_utilization: Optional[float] = Field(None, gt=0.0, le=1.0)
    enforce_eager: Optional[bool] = None
    hf_token: Optional[str] = None

    @field_validator("model_id")
    @classmethod
    def validate_model_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("model_id cannot be empty")
        val = v.strip()
        # Strictly reject path traversal sequences and sensitive root paths
        if ".." in val or val.startswith(("/etc", "/root", "/var", "/bin", "/sbin", "/proc", "/sys", "/dev")):
            raise ValueError(f"Path traversal or restricted system path detected in model_id: {val}")
        return val

    @field_validator("quantization")
    @classmethod
    def validate_quantization(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        clean = v.strip().lower()
        if clean in ("", "none"):
            return "none"
        allowed = {"awq", "gptq", "squeezellm", "bitsandbytes", "fp8"}
        if clean not in allowed:
            raise ValueError(f"Invalid quantization '{v}'. Allowed: {sorted(allowed)} or 'none'")
        return clean
