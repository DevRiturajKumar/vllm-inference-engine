import pytest
import time
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.engine import get_vllm_manager, VLLMManager
from app.thinking import parse_thinking_content

@pytest.fixture(autouse=True)
def cleanup():
    VLLMManager.reset()
    yield
    VLLMManager.reset()

client = TestClient(app)

# ==============================================================================
# 1. Path Traversal & Restricted Paths (LFI/RFI)
# ==============================================================================

@pytest.mark.parametrize("malicious_id", [
    "../../../../etc/passwd",
    "../etc/shadow",
    "../../windows/win.ini",
    "/etc/passwd",
    "/root/.ssh/id_rsa",
    "/var/log/auth.log",
    "/dev/urandom",
    "/sys/class",
    "/proc/self/environ",
])
def test_path_traversal_in_load_model(malicious_id):
    response = client.post("/admin/load-model", json={"model_id": malicious_id})
    assert response.status_code == 422
    assert "Path traversal" in str(response.json()) or "restricted" in str(response.json())

@pytest.mark.parametrize("malicious_id", [
    "..%2F..%2Fetc%2Fpasswd",
    "../../etc/passwd",
    "/etc/passwd",
    "/root/.ssh/id_rsa",
])
def test_path_traversal_in_switch_model_get(malicious_id):
    response = client.get(f"/admin/switch-model/{malicious_id}")
    # Path traversal attempts either resolve to 400/422 or are blocked by HTTP path normalization (404)
    assert response.status_code in (400, 404, 422)

def test_empty_model_id_rejected():
    res1 = client.post("/admin/load-model", json={"model_id": ""})
    assert res1.status_code == 422

    res2 = client.post("/admin/load-model", json={"model_id": "   "})
    assert res2.status_code == 422

# ==============================================================================
# 2. Parameter Boundary Violations & Type Safety
# ==============================================================================

@pytest.mark.parametrize("invalid_util", [-0.5, 0.0, 1.1, 5.0, 100.0])
def test_gpu_memory_utilization_bounds(invalid_util):
    response = client.post("/admin/load-model", json={
        "model_id": "Qwen/Qwen2.5-1.5B-Instruct",
        "gpu_memory_utilization": invalid_util
    })
    assert response.status_code == 422

@pytest.mark.parametrize("invalid_len", [-100, 0, 200000, 1000000])
def test_max_model_len_bounds(invalid_len):
    response = client.post("/admin/load-model", json={
        "model_id": "Qwen/Qwen2.5-1.5B-Instruct",
        "max_model_len": invalid_len
    })
    assert response.status_code == 422

def test_invalid_quantization_enum_rejected():
    response = client.post("/admin/load-model", json={
        "model_id": "Qwen/Qwen2.5-1.5B-Instruct",
        "quantization": "malicious_format; rm -rf /"
    })
    assert response.status_code == 422
    assert "Invalid quantization" in str(response.json())

@pytest.mark.parametrize("invalid_temp", [-1.0, 2.5, 100.0])
def test_chat_temperature_bounds(invalid_temp):
    response = client.post("/v1/chat/completions", json={
        "messages": [{"role": "user", "content": "hi"}],
        "temperature": invalid_temp
    })
    assert response.status_code == 422

@pytest.mark.parametrize("invalid_top_p", [-0.1, 0.0, 1.1, 2.0])
def test_chat_top_p_bounds(invalid_top_p):
    response = client.post("/v1/chat/completions", json={
        "messages": [{"role": "user", "content": "hi"}],
        "top_p": invalid_top_p
    })
    assert response.status_code == 422

@pytest.mark.parametrize("invalid_top_k", [-5, 10000])
def test_chat_top_k_bounds(invalid_top_k):
    response = client.post("/v1/chat/completions", json={
        "messages": [{"role": "user", "content": "hi"}],
        "top_k": invalid_top_k
    })
    assert response.status_code == 422

@pytest.mark.parametrize("invalid_tokens", [-10, 0, 100000])
def test_chat_max_tokens_bounds(invalid_tokens):
    response = client.post("/v1/chat/completions", json={
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": invalid_tokens
    })
    assert response.status_code == 422

@pytest.mark.parametrize("invalid_penalty", [-1.0, 0.0, 3.0])
def test_chat_repetition_penalty_bounds(invalid_penalty):
    response = client.post("/v1/chat/completions", json={
        "messages": [{"role": "user", "content": "hi"}],
        "repetition_penalty": invalid_penalty
    })
    assert response.status_code == 422

# ==============================================================================
# 3. Input Validation & DoS Mitigation
# ==============================================================================

def test_chat_empty_messages_rejected():
    response = client.post("/v1/chat/completions", json={"messages": []})
    assert response.status_code == 422

def test_chat_empty_role_rejected():
    response = client.post("/v1/chat/completions", json={
        "messages": [{"role": "   ", "content": "hello"}]
    })
    assert response.status_code == 422

def test_completions_empty_prompt_list_rejected():
    response = client.post("/v1/completions", json={"prompt": []})
    assert response.status_code == 422

def test_completions_oversized_batch_rejected():
    oversized = ["What is 2+2?"] * 300
    response = client.post("/v1/completions", json={"prompt": oversized})
    assert response.status_code == 422
    assert "exceeds maximum size" in str(response.json())

# ==============================================================================
# 4. Information Disclosure & Token Redaction
# ==============================================================================

def test_load_model_error_sanitization_token_redaction():
    with patch("app.engine.AsyncLLMEngine.from_engine_args", side_effect=RuntimeError("Auth failed: hf_SECRETTOKEN1234567890 at https://huggingface.co")):
        response = client.post("/admin/load-model", json={
            "model_id": "meta-llama/Llama-3.2-1B-Instruct",
            "hf_token": "hf_SECRETTOKEN1234567890"
        })
        assert response.status_code == 500
        detail = response.json()["detail"]
        assert "hf_SECRETTOKEN1234567890" not in detail
        assert "hf_***REDACTED***" in detail

# ==============================================================================
# 5. Security Response Headers
# ==============================================================================

def test_security_headers_present():
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.headers["X-Content-Type-Options"] == "nosniff"

# ==============================================================================
# 6. ReDoS Resilience on Thinking Parser
# ==============================================================================

def test_thinking_parser_redos_safety():
    # Construct attack string with repetitive unclosed tags and nested markers
    evil_string = ("<think>" * 500) + ("A" * 5000) + ("</think>" * 200)
    start_time = time.perf_counter()
    reasoning, content = parse_thinking_content(evil_string)
    elapsed = time.perf_counter() - start_time
    assert elapsed < 0.2, f"Regex took too long: {elapsed}s (potential ReDoS)"
    assert reasoning is not None or content is not None

# ==============================================================================
# 7. CORS Security & Credential Reflection Audit
# ==============================================================================

def test_cors_origin_reflection_behavior():
    origin = "https://malicious-site.example"
    response = client.options(
        "/admin/current-model",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        }
    )
    # Audits CORS middleware response headers
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers

# ==============================================================================
# 8. Unauthenticated Access & State Mutation Audit (VAPT Probes)
# ==============================================================================

def test_unauthenticated_admin_endpoints_accessible():
    # Probes that admin plane currently responds without API key / Bearer token
    res = client.get("/admin/current-model")
    assert res.status_code == 200
    assert "is_loaded" in res.json()

def test_unauthenticated_unload_model_accessible():
    # Demonstrates that unauthenticated callers can trigger model unloads
    res = client.post("/admin/unload-model")
    assert res.status_code == 200
    assert res.json()["status"] == "UNLOADED"

def test_csrf_state_change_via_get_unload_accessible():
    # Demonstrates that unload endpoint is reachable via GET (CSRF vector)
    res = client.get("/admin/unload-model")
    assert res.status_code == 200
    assert res.json()["status"] == "UNLOADED"

# ==============================================================================
# 9. Hardware & System Information Disclosure Probe
# ==============================================================================

def test_unauthenticated_health_reveals_topology():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "gpu_available" in data
    assert "vram_allocated_gb" in data
    assert "vram_total_gb" in data

# ==============================================================================
# 10. Advanced Input Boundary & NaN/Inf Injection Tests
# ==============================================================================

def test_chat_nan_temperature_rejected():
    from app.schemas.requests import ChatCompletionRequest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        ChatCompletionRequest(
            messages=[{"role": "user", "content": "hello"}],
            temperature=float("nan")
        )

    with pytest.raises(ValidationError):
        ChatCompletionRequest(
            messages=[{"role": "user", "content": "hello"}],
            temperature=float("inf")
        )

def test_load_model_invalid_dtype_rejected():
    res = client.post("/admin/load-model", json={
        "model_id": "Qwen/Qwen2.5-1.5B-Instruct",
        "dtype": "malicious_script_injection"
    })
    assert res.status_code == 422
    assert "Invalid dtype" in str(res.json())
