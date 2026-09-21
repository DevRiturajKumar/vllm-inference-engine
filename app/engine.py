import gc
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional
import torch
from transformers import AutoTokenizer
from app.config import get_settings

try:
    from vllm import AsyncLLMEngine, AsyncEngineArgs, SamplingParams
except ImportError:
    class AsyncLLMEngine:
        @classmethod
        def from_engine_args(cls, *args, **kwargs):
            raise RuntimeError("vLLM is not installed or available.")

    class AsyncEngineArgs:
        def __init__(self, *args, **kwargs):
            pass

    class SamplingParams:
        def __init__(
            self,
            max_tokens: int = 512,
            temperature: float = 0.7,
            top_p: float = 0.9,
            top_k: int = 50,
            repetition_penalty: float = 1.05,
            stop: Optional[Any] = None,
            **kwargs,
        ):
            self.max_tokens = max_tokens
            self.temperature = temperature
            self.top_p = top_p
            self.top_k = top_k
            self.repetition_penalty = repetition_penalty
            self.stop = stop
            for k, v in kwargs.items():
                setattr(self, k, v)

class VLLMManager:
    _instance: Optional["VLLMManager"] = None
    _lock: asyncio.Lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self.engine: Optional[Any] = None
        self.tokenizer: Optional[Any] = None
        self.model_id: Optional[str] = None
        self.active_config: Dict[str, Any] = {}
        self.is_loading: bool = False
        self.loading_model_id: Optional[str] = None

    @classmethod
    def reset(cls):
        cls._instance = None

    def is_loaded(self) -> bool:
        return self.engine is not None and self.model_id is not None

    async def load_model(
        self,
        model_id: str,
        quantization: Optional[str] = None,
        max_model_len: Optional[int] = None,
        gpu_memory_utilization: Optional[float] = None,
        enforce_eager: Optional[bool] = None,
        hf_token: Optional[str] = None,
        dtype: Optional[str] = None,
    ) -> Dict[str, Any]:
        async with self._lock:
            settings = get_settings()

            if self.is_loaded():
                await self._unload_internal()

            self.is_loading = True
            self.loading_model_id = model_id

            try:
                quant = quantization or settings.QUANTIZATION
                quant = None if quant in ("none", "", None) else quant
                token = hf_token or settings.HF_TOKEN
                max_len = max_model_len or settings.MAX_MODEL_LEN
                gpu_mem = gpu_memory_utilization or settings.GPU_MEMORY_UTILIZATION
                eager = enforce_eager if enforce_eager is not None else settings.ENFORCE_EAGER

                # Smart dtype resolution:
                # If dtype is "auto" (or None) and GPU does not support bfloat16 (like Tesla T4),
                # resolve to "float16" to avoid vLLM upcasting to float32 (which crashes with 80KB SRAM limit on Gemma 2).
                # On A100/L4, torch.cuda.is_bf16_supported() is True, so it keeps "auto" / "bfloat16".
                target_dtype = dtype or settings.DTYPE
                if target_dtype in ("auto", None) and torch.cuda.is_available():
                    if hasattr(torch.cuda, "is_bf16_supported") and not torch.cuda.is_bf16_supported():
                        resolved_dtype = "float16"
                    else:
                        resolved_dtype = "auto"
                else:
                    resolved_dtype = target_dtype or "auto"

                engine_args = AsyncEngineArgs(
                    model=model_id,
                    revision=settings.MODEL_REVISION,
                    quantization=quant,
                    dtype=resolved_dtype,
                    max_model_len=max_len,
                    gpu_memory_utilization=gpu_mem,
                    enforce_eager=eager,
                    tensor_parallel_size=settings.TENSOR_PARALLEL_SIZE,
                    trust_remote_code=settings.TRUST_REMOTE_CODE,
                    enable_prefix_caching=settings.ENABLE_PREFIX_CACHING,
                    download_dir=settings.CACHE_DIR,
                )

                # Offload heavy/blocking engine instantiation & tokenizer download to worker thread
                engine = await asyncio.to_thread(AsyncLLMEngine.from_engine_args, engine_args)
                tokenizer = await asyncio.to_thread(
                    AutoTokenizer.from_pretrained,
                    model_id,
                    trust_remote_code=settings.TRUST_REMOTE_CODE,
                    token=token,
                )

                self.engine = engine
                self.tokenizer = tokenizer
                self.model_id = model_id
                self.active_config = {
                    "model_id": model_id,
                    "quantization": quant or "none",
                    "dtype": resolved_dtype,
                    "max_model_len": max_len,
                    "gpu_memory_utilization": gpu_mem,
                    "enforce_eager": eager,
                }
                return self.active_config
            finally:
                self.is_loading = False
                self.loading_model_id = None

    async def unload_model(self) -> Dict[str, Any]:
        async with self._lock:
            return await self._unload_internal()

    async def _unload_internal(self) -> Dict[str, Any]:
        prev_model = self.model_id
        self.engine = None
        self.tokenizer = None
        self.model_id = None
        self.active_config = {}

        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()

        return {"status": "UNLOADED", "previous_model": prev_model}

    def build_sampling_params(self, req_data: Dict[str, Any]) -> SamplingParams:
        settings = get_settings()
        raw_temp = req_data.get("temperature")
        temp = settings.DEFAULT_TEMPERATURE if raw_temp is None else float(raw_temp)
        do_sample = req_data.get("do_sample")

        if do_sample is False or temp == 0.0:
            final_temp = 0.0
            top_p = 1.0
            top_k = -1
        else:
            final_temp = max(temp, 1e-4)
            top_p_val = req_data.get("top_p")
            top_p = float(settings.DEFAULT_TOP_P if top_p_val is None else top_p_val)
            top_k_val = req_data.get("top_k")
            top_k = int(settings.DEFAULT_TOP_K if top_k_val is None else top_k_val)

        max_tokens_val = req_data.get("max_tokens")
        max_tokens = int(settings.DEFAULT_MAX_TOKENS if max_tokens_val is None else max_tokens_val)

        rep_pen_val = req_data.get("repetition_penalty")
        repetition_penalty = float(settings.DEFAULT_REPETITION_PENALTY if rep_pen_val is None else rep_pen_val)

        stop = req_data.get("stop")
        if isinstance(stop, str):
            stop = [stop]

        return SamplingParams(
            max_tokens=max_tokens,
            temperature=final_temp,
            top_p=top_p,
            top_k=top_k,
            repetition_penalty=repetition_penalty,
            stop=stop,
        )

def get_vllm_manager() -> VLLMManager:
    return VLLMManager()
