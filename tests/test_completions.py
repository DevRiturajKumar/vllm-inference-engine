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

def test_completions_unloaded_returns_503():
    client = TestClient(app)
    response = client.post("/v1/completions", json={
        "prompt": "Tell me a joke"
    })
    assert response.status_code == 503
    assert "No model is currently loaded" in response.json()["detail"]

def test_completions_single_prompt():
    vm = get_vllm_manager()
    vm.model_id = "test-model"

    async def mock_generate(prompt, sampling_params, req_id):
        mock_output = MagicMock()
        mock_choice = MagicMock()
        mock_choice.text = "generated response"
        mock_choice.token_ids = [11, 22]
        mock_choice.finish_reason = "stop"
        mock_output.outputs = [mock_choice]
        mock_output.prompt_token_ids = [1, 2, 3]
        yield mock_output

    mock_engine = MagicMock()
    mock_engine.generate = mock_generate
    vm.engine = mock_engine

    client = TestClient(app)
    response = client.post("/v1/completions", json={
        "prompt": "Once upon a time",
        "stream": False
    })
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "text_completion"
    assert data["model"] == "test-model"
    assert len(data["choices"]) == 1
    assert data["choices"][0]["text"] == "generated response"
    assert data["choices"][0]["index"] == 0
    assert data["usage"]["prompt_tokens"] == 3
    assert data["usage"]["completion_tokens"] == 2
    assert data["usage"]["total_tokens"] == 5

def test_completions_prompt_list():
    vm = get_vllm_manager()
    vm.model_id = "test-model"

    async def mock_generate(prompt, sampling_params, req_id):
        mock_output = MagicMock()
        mock_choice = MagicMock()
        mock_choice.text = f"echo {prompt}"
        mock_choice.token_ids = [100]
        mock_choice.finish_reason = "stop"
        mock_output.outputs = [mock_choice]
        mock_output.prompt_token_ids = [1, 2]
        yield mock_output

    mock_engine = MagicMock()
    mock_engine.generate = mock_generate
    vm.engine = mock_engine

    client = TestClient(app)
    response = client.post("/v1/completions", json={
        "prompt": ["Prompt A", "Prompt B"],
        "stream": False
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["choices"]) == 2
    assert data["choices"][0]["text"] == "echo Prompt A"
    assert data["choices"][1]["text"] == "echo Prompt B"
    assert data["usage"]["prompt_tokens"] == 4
    assert data["usage"]["completion_tokens"] == 2

def test_completions_streaming():
    vm = get_vllm_manager()
    vm.model_id = "test-model"

    async def mock_generate(prompt, sampling_params, req_id):
        mock_output = MagicMock()
        mock_choice = MagicMock()
        mock_choice.text = "chunk text"
        mock_output.outputs = [mock_choice]
        yield mock_output

    mock_engine = MagicMock()
    mock_engine.generate = mock_generate
    vm.engine = mock_engine

    client = TestClient(app)
    response = client.post("/v1/completions", json={
        "prompt": "Stream prompt",
        "stream": True
    })
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert "chunk text" in response.text
    assert "data: [DONE]" in response.text
