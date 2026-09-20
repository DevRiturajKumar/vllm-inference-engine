import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.engine import get_vllm_manager, VLLMManager

@pytest.fixture(autouse=True)
def cleanup():
    VLLMManager.reset()
    yield
    VLLMManager.reset()

def test_admin_load_model_success():
    vm = get_vllm_manager()
    mock_engine = MagicMock()
    mock_tokenizer = MagicMock()

    with patch("app.engine.AsyncEngineArgs"), \
         patch("app.engine.AsyncLLMEngine.from_engine_args", return_value=mock_engine), \
         patch("app.engine.AutoTokenizer.from_pretrained", return_value=mock_tokenizer):

        client = TestClient(app)
        response = client.post("/admin/load-model", json={
            "model_id": "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
            "quantization": "none",
            "max_model_len": 2048,
            "gpu_memory_utilization": 0.8,
            "enforce_eager": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "LOADED"
        assert data["details"]["model_id"] == "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
        assert vm.is_loaded() is True

def test_admin_load_model_failure():
    with patch("app.engine.AsyncLLMEngine.from_engine_args", side_effect=RuntimeError("CUDA out of memory")):
        client = TestClient(app)
        response = client.post("/admin/load-model", json={
            "model_id": "faulty-model"
        })
        assert response.status_code == 500
        assert "CUDA out of memory" in response.json()["detail"]

def test_admin_unload_model():
    vm = get_vllm_manager()
    vm.model_id = "test-model"
    vm.engine = MagicMock()

    client = TestClient(app)
    response = client.post("/admin/unload-model")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UNLOADED"
    assert data["details"]["previous_model"] == "test-model"
    assert vm.is_loaded() is False

def test_admin_unload_model_get():
    vm = get_vllm_manager()
    vm.model_id = "test-model"
    vm.engine = MagicMock()

    client = TestClient(app)
    response = client.get("/admin/unload-model")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UNLOADED"
    assert vm.is_loaded() is False

def test_admin_hotswap_model():
    vm = get_vllm_manager()
    mock_engine = MagicMock()
    mock_tokenizer = MagicMock()

    with patch("app.engine.AsyncEngineArgs"), \
         patch("app.engine.AsyncLLMEngine.from_engine_args", return_value=mock_engine), \
         patch("app.engine.AutoTokenizer.from_pretrained", return_value=mock_tokenizer):

        client = TestClient(app)
        res1 = client.post("/admin/load-model", json={"model_id": "model-alpha"})
        assert res1.status_code == 200
        assert vm.model_id == "model-alpha"

        res2 = client.post("/admin/load-model", json={"model_id": "model-beta"})
        assert res2.status_code == 200
        assert vm.model_id == "model-beta"

def test_admin_switch_model_get():
    vm = get_vllm_manager()
    mock_engine = MagicMock()
    mock_tokenizer = MagicMock()

    with patch("app.engine.AsyncEngineArgs"), \
         patch("app.engine.AsyncLLMEngine.from_engine_args", return_value=mock_engine), \
         patch("app.engine.AutoTokenizer.from_pretrained", return_value=mock_tokenizer):

        client = TestClient(app)
        response = client.get("/admin/switch-model/Qwen/Qwen2.5-3B-Instruct")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "LOADED"
        assert data["details"]["model_id"] == "Qwen/Qwen2.5-3B-Instruct"
        assert vm.model_id == "Qwen/Qwen2.5-3B-Instruct"

def test_admin_current_model():
    vm = get_vllm_manager()
    client = TestClient(app)

    res1 = client.get("/admin/current-model")
    assert res1.status_code == 200
    assert res1.json()["is_loaded"] is False

    vm.model_id = "test-model"
    vm.engine = MagicMock()
    vm.active_config = {"model_id": "test-model"}

    res2 = client.get("/admin/current-model")
    assert res2.status_code == 200
    assert res2.json()["is_loaded"] is True
    assert res2.json()["model_id"] == "test-model"
