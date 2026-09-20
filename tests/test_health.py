import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.engine import get_vllm_manager, VLLMManager

@pytest.fixture(autouse=True)
def cleanup():
    VLLMManager.reset()
    yield
    VLLMManager.reset()

def test_health_unloaded():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "READY_NO_MODEL"
    assert data["loaded_model"] is None

def test_health_loaded_with_gpu():
    vm = get_vllm_manager()
    vm.model_id = "Qwen/Qwen2.5-1.5B-Instruct"
    vm.engine = MagicMock()

    mock_props = MagicMock()
    mock_props.total_memory = 16 * (1024 ** 3)

    with patch("torch.cuda.is_available", return_value=True), \
         patch("torch.cuda.get_device_name", return_value="Tesla T4"), \
         patch("torch.cuda.memory_allocated", return_value=5 * (1024 ** 3)), \
         patch("torch.cuda.get_device_properties", return_value=mock_props):

        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "OK"
        assert data["loaded_model"] == "Qwen/Qwen2.5-1.5B-Instruct"
        assert data["gpu_available"] is True
        assert data["gpu_name"] == "Tesla T4"
        assert data["vram_allocated_gb"] == 5.0
        assert data["vram_total_gb"] == 16.0
