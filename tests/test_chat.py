import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.engine import get_vllm_manager, VLLMManager

@pytest.fixture(autouse=True)
def cleanup():
    VLLMManager.reset()
    yield
    VLLMManager.reset()

def test_chat_unloaded_returns_503():
    client = TestClient(app)
    response = client.post("/v1/chat/completions", json={
        "messages": [{"role": "user", "content": "Hello"}]
    })
    assert response.status_code == 503
    assert "No model is currently loaded" in response.json()["detail"]

def test_chat_non_streaming():
    vm = get_vllm_manager()
    vm.model_id = "test-model"

    mock_tokenizer = MagicMock()
    mock_tokenizer.apply_chat_template.return_value = "<user>Hello<assistant>"
    vm.tokenizer = mock_tokenizer

    async def mock_generate(prompt, sampling_params, req_id):
        mock_output = MagicMock()
        mock_choice = MagicMock()
        mock_choice.text = "Hello back!"
        mock_choice.token_ids = [1, 2]
        mock_choice.finish_reason = "stop"
        mock_output.outputs = [mock_choice]
        mock_output.prompt_token_ids = [10, 20, 30]
        yield mock_output

    mock_engine = MagicMock()
    mock_engine.generate = mock_generate
    vm.engine = mock_engine

    client = TestClient(app)
    response = client.post("/v1/chat/completions", json={
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": False
    })
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "chat.completion"
    assert data["model"] == "test-model"
    assert len(data["choices"]) == 1
    assert data["choices"][0]["message"]["content"] == "Hello back!"
    assert data["choices"][0]["finish_reason"] == "stop"
    assert data["usage"]["prompt_tokens"] == 3
    assert data["usage"]["completion_tokens"] == 2
    assert data["usage"]["total_tokens"] == 5

def test_chat_streaming():
    vm = get_vllm_manager()
    vm.model_id = "test-model"

    mock_tokenizer = MagicMock()
    mock_tokenizer.apply_chat_template.return_value = "<user>Stream<assistant>"
    vm.tokenizer = mock_tokenizer

    async def mock_generate(prompt, sampling_params, req_id):
        first = MagicMock()
        first_choice = MagicMock()
        first_choice.text = "Part 1"
        first.outputs = [first_choice]
        yield first

        second = MagicMock()
        second_choice = MagicMock()
        second_choice.text = "Part 1 Part 2"
        second.outputs = [second_choice]
        yield second

    mock_engine = MagicMock()
    mock_engine.generate = mock_generate
    vm.engine = mock_engine

    client = TestClient(app)
    response = client.post("/v1/chat/completions", json={
        "messages": [{"role": "user", "content": "Stream"}],
        "stream": True
    })
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    text = response.text
    assert "data: " in text
    assert "data: [DONE]" in text
    assert "Part 1" in text
    assert "Part 2" in text

def test_chat_with_thinking_enabled():
    vm = get_vllm_manager()
    vm.model_id = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"

    mock_tokenizer = MagicMock()
    mock_tokenizer.apply_chat_template.return_value = "prompt"
    vm.tokenizer = mock_tokenizer

    async def mock_generate(prompt, sampling_params, req_id):
        mock_output = MagicMock()
        mock_choice = MagicMock()
        mock_choice.text = "<think>Let me calculate 2+2.</think>2 + 2 = 4."
        mock_choice.token_ids = [1, 2, 3]
        mock_choice.finish_reason = "stop"
        mock_output.outputs = [mock_choice]
        mock_output.prompt_token_ids = [10]
        yield mock_output

    mock_engine = MagicMock()
    mock_engine.generate = mock_generate
    vm.engine = mock_engine

    client = TestClient(app)
    response = client.post("/v1/chat/completions", json={
        "messages": [{"role": "user", "content": "What is 2+2?"}],
        "enable_thinking": True,
        "stream": False
    })
    assert response.status_code == 200
    data = response.json()
    msg = data["choices"][0]["message"]
    assert msg["content"] == "2 + 2 = 4."
    assert msg["reasoning"] == "Let me calculate 2+2."
    assert msg["reasoning_content"] == "Let me calculate 2+2."

def test_chat_with_thinking_disabled():
    vm = get_vllm_manager()
    vm.model_id = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"

    mock_tokenizer = MagicMock()
    mock_tokenizer.apply_chat_template.return_value = "prompt"
    vm.tokenizer = mock_tokenizer

    async def mock_generate(prompt, sampling_params, req_id):
        mock_output = MagicMock()
        mock_choice = MagicMock()
        mock_choice.text = "<think>Let me calculate 2+2.</think>2 + 2 = 4."
        mock_choice.token_ids = [1, 2, 3]
        mock_choice.finish_reason = "stop"
        mock_output.outputs = [mock_choice]
        mock_output.prompt_token_ids = [10]
        yield mock_output

    mock_engine = MagicMock()
    mock_engine.generate = mock_generate
    vm.engine = mock_engine

    client = TestClient(app)
    response = client.post("/v1/chat/completions", json={
        "messages": [{"role": "user", "content": "What is 2+2?"}],
        "thinking": {"type": "disabled"},
        "stream": False
    })
    assert response.status_code == 200
    data = response.json()
    msg = data["choices"][0]["message"]
    assert msg["content"] == "2 + 2 = 4."
    assert "reasoning" not in msg

def test_chat_streaming_with_thinking():
    vm = get_vllm_manager()
    vm.model_id = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"

    mock_tokenizer = MagicMock()
    mock_tokenizer.apply_chat_template.return_value = "prompt"
    vm.tokenizer = mock_tokenizer

    async def mock_generate(prompt, sampling_params, req_id):
        out1 = MagicMock()
        c1 = MagicMock()
        c1.text = "<think>Thinking"
        out1.outputs = [c1]
        yield out1

        out2 = MagicMock()
        c2 = MagicMock()
        c2.text = "<think>Thinking more</think>Answer"
        out2.outputs = [c2]
        yield out2

    mock_engine = MagicMock()
    mock_engine.generate = mock_generate
    vm.engine = mock_engine

    client = TestClient(app)
    response = client.post("/v1/chat/completions", json={
        "messages": [{"role": "user", "content": "What is 2+2?"}],
        "enable_thinking": True,
        "stream": True
    })
    assert response.status_code == 200
    text = response.text
    assert "reasoning" in text

def test_chat_respects_default_enable_thinking_env(monkeypatch):
    monkeypatch.setenv("DEFAULT_ENABLE_THINKING", "false")
    from app.config import get_settings
    get_settings.cache_clear()
    try:
        vm = get_vllm_manager()
        vm.model_id = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"

        mock_tokenizer = MagicMock()
        mock_tokenizer.apply_chat_template.return_value = "prompt"
        vm.tokenizer = mock_tokenizer

        async def mock_generate(prompt, sampling_params, req_id):
            mock_output = MagicMock()
            mock_choice = MagicMock()
            mock_choice.text = "Direct answer."
            mock_choice.token_ids = [1, 2]
            mock_choice.finish_reason = "stop"
            mock_output.outputs = [mock_choice]
            mock_output.prompt_token_ids = [10]
            yield mock_output

        mock_engine = MagicMock()
        mock_engine.generate = mock_generate
        vm.engine = mock_engine

        client = TestClient(app)
        response = client.post("/v1/chat/completions", json={
            "messages": [{"role": "user", "content": "What is 2+2?"}],
            "stream": False
        })
        assert response.status_code == 200
        _, kwargs = mock_tokenizer.apply_chat_template.call_args
        assert kwargs.get("enable_thinking") is False
    finally:
        get_settings.cache_clear()
