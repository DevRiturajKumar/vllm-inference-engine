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

def test_models_unloaded():
    client = TestClient(app)
    response = client.get("/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert data["data"] == []

def test_models_loaded():
    vm = get_vllm_manager()
    vm.model_id = "Qwen/Qwen2.5-1.5B-Instruct"
    vm.engine = MagicMock()

    client = TestClient(app)
    response = client.get("/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert len(data["data"]) == 1
    assert data["data"][0]["id"] == "Qwen/Qwen2.5-1.5B-Instruct"
    assert data["data"][0]["object"] == "model"
    assert data["data"][0]["owned_by"] == "vllm"
