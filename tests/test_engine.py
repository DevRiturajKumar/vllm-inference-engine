import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.engine import VLLMManager, get_vllm_manager

@pytest.fixture(autouse=True)
def reset_manager():
    VLLMManager.reset()
    yield
    VLLMManager.reset()

def test_singleton_pattern():
    m1 = get_vllm_manager()
    m2 = get_vllm_manager()
    m3 = VLLMManager()
    assert m1 is m2
    assert m2 is m3

def test_is_loaded_initial():
    m = get_vllm_manager()
    assert m.is_loaded() is False
    assert m.model_id is None
    assert m.engine is None

def test_build_sampling_params():
    m = get_vllm_manager()
    params = m.build_sampling_params({
        "max_tokens": 100,
        "temperature": 0.8,
        "top_p": 0.95,
        "top_k": 40,
        "repetition_penalty": 1.1,
        "stop": ["END"]
    })
    assert params.max_tokens == 100
    assert params.temperature == 0.8
    assert params.top_p == 0.95
    assert params.top_k == 40
    assert params.repetition_penalty == 1.1
    assert params.stop == ["END"]

@pytest.mark.anyio
async def test_unload_model_lifecycle():
    m = get_vllm_manager()
    m.engine = MagicMock()
    m.model_id = "test-model"
    m.tokenizer = MagicMock()
    m.active_config = {"model_id": "test-model"}
    assert m.is_loaded() is True

    result = await m.unload_model()
    assert result["status"] == "UNLOADED"
    assert result["previous_model"] == "test-model"
    assert m.is_loaded() is False
    assert m.engine is None
    assert m.tokenizer is None
    assert m.model_id is None
    assert m.active_config == {}

@pytest.mark.anyio
async def test_load_model_with_mock():
    m = get_vllm_manager()
    mock_engine = MagicMock()
    mock_tokenizer = MagicMock()

    with patch("app.engine.AsyncEngineArgs") as mock_args_cls, \
         patch("app.engine.AsyncLLMEngine") as mock_engine_cls, \
         patch("app.engine.AutoTokenizer.from_pretrained", return_value=mock_tokenizer):

        mock_engine_cls.from_engine_args.return_value = mock_engine

        result = await m.load_model("test-model-hf")
        assert result["model_id"] == "test-model-hf"
        assert m.is_loaded() is True
        assert m.engine is mock_engine
        assert m.tokenizer is mock_tokenizer
