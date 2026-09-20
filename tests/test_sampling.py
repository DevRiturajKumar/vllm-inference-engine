import pytest
from app.engine import get_vllm_manager, VLLMManager
from app.config import get_settings

@pytest.fixture(autouse=True)
def cleanup():
    VLLMManager.reset()
    yield
    VLLMManager.reset()

def test_sampling_defaults():
    vm = get_vllm_manager()
    settings = get_settings()
    params = vm.build_sampling_params({})
    assert params.max_tokens == settings.DEFAULT_MAX_TOKENS
    assert params.temperature == settings.DEFAULT_TEMPERATURE
    assert params.top_p == settings.DEFAULT_TOP_P
    assert params.top_k == settings.DEFAULT_TOP_K
    assert params.repetition_penalty == settings.DEFAULT_REPETITION_PENALTY
    assert params.stop is None

def test_temperature_zero_disables_sampling():
    vm = get_vllm_manager()
    params = vm.build_sampling_params({"temperature": 0.0})
    assert params.temperature == 0.0
    assert params.top_p == 1.0
    assert params.top_k == -1

def test_do_sample_false_disables_sampling():
    vm = get_vllm_manager()
    params = vm.build_sampling_params({"do_sample": False, "temperature": 0.7})
    assert params.temperature == 0.0
    assert params.top_p == 1.0
    assert params.top_k == -1

def test_temperature_clamping():
    vm = get_vllm_manager()
    params = vm.build_sampling_params({"temperature": 0.000001})
    assert params.temperature == 1e-4

def test_stop_sequence_string_conversion():
    vm = get_vllm_manager()
    params1 = vm.build_sampling_params({"stop": "<|im_end|>"})
    assert params1.stop == ["<|im_end|>"]

    params2 = vm.build_sampling_params({"stop": ["<|im_end|>", "STOP"]})
    assert params2.stop == ["<|im_end|>", "STOP"]

def test_custom_token_limits_and_penalty():
    vm = get_vllm_manager()
    params = vm.build_sampling_params({
        "max_tokens": 1024,
        "repetition_penalty": 1.25,
        "top_p": 0.85,
        "top_k": 20
    })
    assert params.max_tokens == 1024
    assert params.repetition_penalty == 1.25
    assert params.top_p == 0.85
    assert params.top_k == 20
