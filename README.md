# Production vLLM FastAPI Inference Engine & Cloudflare Quick Tunnel

A lean, high-throughput, model-agnostic LLM Inference Engine powered strictly by **vLLM (AsyncLLMEngine >= 0.6.0)** and **FastAPI**.

Designed for instant deployment in **Google Colab** (NVIDIA T4, L4, A100) or self-hosted GPU servers, exposed publicly via **Cloudflare Quick Tunnel (`trycloudflare.com`)** or run strictly on **localhost** via environment toggles.

---

## ⚡ Core Architecture

- **Zero Startup Lag (No Default Model)**: Starts in milliseconds in standby mode (`status: "READY_NO_MODEL"`). Immediately prints the public Cloudflare Quick Tunnel URL and Swagger UI (`/docs`).
- **Dynamic Model Lifecycle**: Hot-swap or load models on the fly via `POST /admin/load-model` and release all VRAM back to 0 MB with `POST /admin/unload-model`.
- **PagedAttention & Continuous Batching**: High-concurrency generation with chunked prefill, RadixAutomatic Prefix Caching (APC), and Server-Sent Events (SSE).
- **DeepSeek Reasoning First-Class Support**: Native parsing of `<think>` and `</think>` chain-of-thought tokens for DeepSeek-R1 and QwQ models.
- **100% Configurable via `.env`**: Network ports, CORS, memory fractions, context windows, and fallback behaviors.
- **Enterprise Security (VAPT-Audited)**: Path traversal rejection, finite numeric bounds, secret redaction, and defensive HTTP security headers (`nosniff`, `DENY`, `strict-origin`).
- **Portable Web UI**: Standalone React + Lucide React + Tailwind SPA located in `frontend/`.

---

## 🚀 Quick Start

### Option A: Google Colab (One-Click Launch)

**Method 1: Direct Zip Upload (Recommended — No Token Needed)**
1. Zip this project folder locally: `zip -r vllm-engine.zip . -x "node_modules/*" ".git/*"`
2. Upload `vllm-engine.zip` to Colab and execute:
```bash
!unzip -q vllm-engine.zip -d vllm-inference-engine
%cd vllm-inference-engine
!sed -i 's/\r$//' run_colab.sh && bash run_colab.sh
```

**Method 2: Private GitHub Repository Clone (via `.env`)**
If cloning directly from your private GitHub repository in Colab, configure your `.env`:
```ini
GITHUB_TOKEN=ghp_yourPersonalAccessToken
REPO_URL=https://github.com/your-username/vllm-inference-engine.git
```
Then run:
```bash
!sed -i 's/\r$//' run_colab.sh && bash run_colab.sh
```
`run_colab.sh` reads `GITHUB_TOKEN` and `REPO_URL` directly from `.env`, clones the private repo, starts the Cloudflare Quick Tunnel, and boots the engine.

When running, it automatically starts the Cloudflare Quick Tunnel and outputs:
```text
==================================================================
 🌐 Cloudflare Quick Tunnel Live: https://xxx-yyy-zzz.trycloudflare.com
 📚 Swagger UI Documentation:    https://xxx-yyy-zzz.trycloudflare.com/docs
 💻 Local Address:               http://localhost:8006
==================================================================
```

### Option B: Local or Self-Hosted GPU
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy and customize configuration
cp .env.example .env

# 3. Start server (starts idle on localhost)
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8006
```

---

## 📋 Complete Supported Model Catalog (Copy-Pasteable)

All models below have native, readymade support in vLLM. You can copy-paste any `model_id` directly into the `/admin/load-model` endpoint or the Web UI.

### 1. Qwen 2.5 Series (General Purpose & Coding)

| Model Name | Hugging Face Model ID | Quantization | Context | Min VRAM | Recommended GPU |
|---|---|---|---|---|---|
| **Qwen 2.5 0.5B Instruct** | `Qwen/Qwen2.5-0.5B-Instruct` | `none` | 32,768 | ~3.5 GB | T4 / L4 / A100 |
| **Qwen 2.5 0.5B AWQ** | `Qwen/Qwen2.5-0.5B-Instruct-AWQ` | `awq` | 32,768 | ~2.5 GB | T4 / L4 / A100 |
| **Qwen 2.5 1.5B Instruct** | `Qwen/Qwen2.5-1.5B-Instruct` | `none` | 32,768 | ~5.8 GB | T4 / L4 / A100 |
| **Qwen 2.5 1.5B AWQ** | `Qwen/Qwen2.5-1.5B-Instruct-AWQ` | `awq` | 32,768 | ~3.8 GB | T4 / L4 / A100 |
| **Qwen 2.5 3B Instruct** | `Qwen/Qwen2.5-3B-Instruct` | `none` | 16,384 | ~9.5 GB | T4 / L4 / A100 |
| **Qwen 2.5 3B AWQ** | `Qwen/Qwen2.5-3B-Instruct-AWQ` | `awq` | 32,768 | ~5.5 GB | T4 / L4 / A100 |
| **Qwen 2.5 7B Instruct** | `Qwen/Qwen2.5-7B-Instruct` | `none` | 16,384 | ~19.5 GB | L4 / A100 |
| **Qwen 2.5 7B AWQ (4-bit)** | `Qwen/Qwen2.5-7B-Instruct-AWQ` | `awq` | 8,192 | ~7.5 GB | T4 / L4 / A100 |
| **Qwen 2.5 14B Instruct** | `Qwen/Qwen2.5-14B-Instruct` | `none` | 16,384 | ~35.0 GB | A100-40GB / A100-80GB |
| **Qwen 2.5 14B AWQ** | `Qwen/Qwen2.5-14B-Instruct-AWQ` | `awq` | 8,192 | ~12.5 GB | T4 (eager) / L4 / A100 |
| **Qwen 2.5 32B Instruct** | `Qwen/Qwen2.5-32B-Instruct` | `none` | 16,384 | ~74.0 GB | A100-80GB |
| **Qwen 2.5 32B AWQ** | `Qwen/Qwen2.5-32B-Instruct-AWQ` | `awq` | 4,096 | ~22.0 GB | L4 (eager) / A100 |
| **Qwen 2.5 72B AWQ** | `Qwen/Qwen2.5-72B-Instruct-AWQ` | `awq` | 8,192 | ~52.0 GB | A100-80GB |
| **Qwen 2.5 Coder 1.5B** | `Qwen/Qwen2.5-Coder-1.5B-Instruct` | `none` | 32,768 | ~5.8 GB | T4 / L4 / A100 |
| **Qwen 2.5 Coder 7B AWQ** | `Qwen/Qwen2.5-Coder-7B-Instruct-AWQ` | `awq` | 8,192 | ~7.5 GB | T4 / L4 / A100 |
| **Qwen 2.5 Coder 14B AWQ**| `Qwen/Qwen2.5-Coder-14B-Instruct-AWQ`| `awq` | 8,192 | ~12.5 GB | T4 (eager) / L4 / A100 |
| **Qwen 2.5 Coder 32B AWQ**| `Qwen/Qwen2.5-Coder-32B-Instruct-AWQ`| `awq` | 4,096 | ~22.0 GB | L4 (eager) / A100 |

---

### 2. DeepSeek R1 & Reasoning Series

*Emits step-by-step `<think>` reasoning tags, automatically parsed and displayed by the engine and Web UI.*

| Model Name | Hugging Face Model ID | Quantization | Context | Min VRAM | Recommended GPU |
|---|---|---|---|---|---|
| **DeepSeek R1 Distill Qwen 1.5B** | `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B` | `none` | 32,768 | ~5.8 GB | T4 / L4 / A100 |
| **DeepSeek R1 Distill Qwen 1.5B AWQ** | `casperhansen/deepseek-r1-distill-qwen-1.5b-awq` | `awq` | 32,768 | ~3.8 GB | T4 / L4 / A100 |
| **DeepSeek R1 Distill Qwen 7B** | `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B` | `none` | 16,384 | ~19.5 GB | L4 / A100 |
| **DeepSeek R1 Distill Qwen 7B AWQ** | `casperhansen/deepseek-r1-distill-qwen-7b-awq` | `awq` | 8,192 | ~7.5 GB | T4 / L4 / A100 |
| **DeepSeek R1 Distill Llama 8B** | `deepseek-ai/DeepSeek-R1-Distill-Llama-8B` | `none` | 16,384 | ~20.0 GB | L4 / A100 |
| **DeepSeek R1 Distill Llama 8B AWQ** | `casperhansen/deepseek-r1-distill-llama-8b-awq` | `awq` | 8,192 | ~8.0 GB | T4 / L4 / A100 |
| **DeepSeek R1 Distill Qwen 14B AWQ**| `casperhansen/deepseek-r1-distill-qwen-14b-awq` | `awq` | 8,192 | ~12.5 GB | T4 (eager) / L4 / A100 |
| **DeepSeek R1 Distill Qwen 32B AWQ**| `casperhansen/deepseek-r1-distill-qwen-32b-awq` | `awq` | 4,096 | ~22.0 GB | L4 (eager) / A100 |
| **DeepSeek R1 Distill Llama 70B AWQ**| `casperhansen/deepseek-r1-distill-llama-70b-awq` | `awq` | 8,192 | ~51.0 GB | A100-80GB |

---

### 3. Meta Llama 3.3, 3.2, 3.1 Series

*(Requires accepting Hugging Face license and supplying `HF_TOKEN`)*

| Model Name | Hugging Face Model ID | Quantization | Context | Min VRAM | Recommended GPU |
|---|---|---|---|---|---|
| **Llama 3.2 1B Instruct** | `meta-llama/Llama-3.2-1B-Instruct` | `none` | 32,768 | ~5.0 GB | T4 / L4 / A100 |
| **Llama 3.2 1B AWQ** | `casperhansen/llama-3.2-1b-instruct-awq` | `awq` | 32,768 | ~3.5 GB | T4 / L4 / A100 |
| **Llama 3.2 3B Instruct** | `meta-llama/Llama-3.2-3B-Instruct` | `none` | 16,384 | ~9.8 GB | T4 / L4 / A100 |
| **Llama 3.2 3B AWQ** | `casperhansen/llama-3.2-3b-instruct-awq` | `awq` | 32,768 | ~5.8 GB | T4 / L4 / A100 |
| **Llama 3.1 8B Instruct** | `meta-llama/Meta-Llama-3.1-8B-Instruct` | `none` | 8,192 | ~20.2 GB | L4 / A100 |
| **Llama 3.1 8B AWQ (4-bit)** | `hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4` | `awq` | 8,192 | ~8.2 GB | T4 / L4 / A100 |
| **Llama 3.1 70B AWQ** | `hugging-quants/Meta-Llama-3.1-70B-Instruct-AWQ-INT4`| `awq` | 8,192 | ~51.0 GB | A100-80GB |
| **Llama 3.3 70B AWQ** | `casperhansen/llama-3.3-70b-instruct-awq` | `awq` | 8,192 | ~51.0 GB | A100-80GB |

---

### 4. Google Gemma 2 & Gemma 3 Series

*(Requires accepting Hugging Face license and supplying `HF_TOKEN`)*

| Model Name | Hugging Face Model ID | Quantization | Context | Min VRAM | Recommended GPU |
|---|---|---|---|---|---|
| **Gemma 2 2B Instruct** | `google/gemma-2-2b-it` | `none` | 8,192 | ~8.0 GB | T4 / L4 / A100 |
| **Gemma 2 2B AWQ** | `TechxGenus/gemma-2b-it-AWQ` | `awq` | 8,192 | ~4.5 GB | T4 / L4 / A100 |
| **Gemma 2 9B Instruct** | `google/gemma-2-9b-it` | `none` | 4,096 | ~21.5 GB | L4 / A100 |
| **Gemma 2 9B AWQ** | `solidrust/gemma-2-9b-it-AWQ` | `awq` | 4,096 | ~11.0 GB | T4 (eager) / L4 / A100 |
| **Gemma 2 27B AWQ** | `mbley/google-gemma-2-27b-it-AWQ` | `awq` | 4,096 | ~21.5 GB | L4 (eager) / A100 |
| **Gemma 3 1B Instruct** | `google/gemma-3-1b-it` | `none` | 32,768 | ~5.2 GB | T4 / L4 / A100 |
| **Gemma 3 4B Instruct** | `google/gemma-3-4b-it` | `none` | 16,384 | ~13.5 GB | T4 (eager) / L4 / A100 |

---

### 5. Mistral & Mixtral Series

| Model Name | Hugging Face Model ID | Quantization | Context | Min VRAM | Recommended GPU |
|---|---|---|---|---|---|
| **Mistral 7B v0.3 Instruct** | `mistralai/Mistral-7B-Instruct-v0.3` | `none` | 8,192 | ~19.0 GB | L4 / A100 |
| **Mistral 7B v0.3 AWQ** | `TechxGenus/Mistral-7B-Instruct-v0.3-AWQ` | `awq` | 8,192 | ~7.2 GB | T4 / L4 / A100 |
| **Mixtral 8x7B AWQ** | `TheBloke/Mixtral-8x7B-Instruct-v0.1-AWQ` | `awq` | 8,192 | ~34.0 GB | A100-40GB / A100-80GB |
| **Ministral 3B Instruct** | `mistralai/Ministral-3-3B-Instruct-2512` | `none` | 16,384 | ~9.8 GB | T4 / L4 / A100 |
| **Ministral 8B Instruct** | `mistralai/Ministral-8B-Instruct-2410` | `none` | 8,192 | ~20.5 GB | L4 / A100 |

---

### 6. Microsoft Phi 3.5 & Phi 4 Series

| Model Name | Hugging Face Model ID | Quantization | Context | Min VRAM | Recommended GPU |
|---|---|---|---|---|---|
| **Phi-3.5-mini Instruct** | `microsoft/Phi-3.5-mini-instruct` | `none` | 8,192 | ~11.8 GB | T4 (eager) / L4 / A100 |
| **Phi-3.5-mini AWQ** | `thesven/Phi-3.5-mini-instruct-awq` | `awq` | 16,384 | ~6.5 GB | T4 / L4 / A100 |
| **Phi-4 (14B)** | `microsoft/phi-4` | `none` | 8,192 | ~34.5 GB | A100-40GB / A100-80GB |
| **Phi-4-mini Instruct** | `microsoft/Phi-4-mini-instruct` | `none` | 8,192 | ~11.8 GB | T4 (eager) / L4 / A100 |

---

## 🎛️ How to Load Models

### 1. Via Swagger UI (`/docs`)
1. Open the public Cloudflare URL: `https://<tunnel-id>.trycloudflare.com/docs`.
2. Expand `POST /admin/load-model`.
3. Paste your desired model configuration:
```json
{
  "model_id": "Qwen/Qwen2.5-1.5B-Instruct",
  "quantization": "none",
  "max_model_len": 4096,
  "gpu_memory_utilization": 0.85,
  "enforce_eager": true,
  "hf_token": null
}
```
4. Click **Execute**. The model will download and initialize in VRAM.

### 2. Via cURL from Terminal
```bash
# Load Model
curl -X POST https://<tunnel-id>.trycloudflare.com/admin/load-model \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
    "max_model_len": 4096,
    "gpu_memory_utilization": 0.85,
    "enforce_eager": true
  }'

# Chat Completion (Streaming)
curl -N -X POST https://<tunnel-id>.trycloudflare.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "What is quantum entanglement?"}],
    "stream": true,
    "max_tokens": 512
  }'

# Unload Model (Free VRAM back to 0 MB)
curl -X POST https://<tunnel-id>.trycloudflare.com/admin/unload-model
```

### 3. Via the Web UI (`frontend/`)
1. Start the frontend: `cd frontend && npm run dev`.
2. Enter your Cloudflare Quick Tunnel URL in the Settings modal.
3. Use the built-in Model Manager modal to select presets or type custom model IDs.

---

## ⚙️ Environment Configuration Reference (`.env`)

| Variable | Default | Description |
|---|---|---|
| `HOST` | `0.0.0.0` | Server bind host. |
| `PORT` | `8006` | Server bind port. |
| `LOG_LEVEL` | `info` | Uvicorn logging level (`debug`, `info`, `warning`, `error`). |
| `CORS_ORIGINS` | `*` | Allowed CORS origins (comma-delimited or `*`). |
| `MODEL_ID` | `null` | Model ID to load on boot (leave empty for idle start). |
| `AUTO_LOAD_ON_STARTUP` | `false` | If `true` and `MODEL_ID` is set, loads model on startup. |
| `MAX_MODEL_LEN` | `4096` | Max sequence context tokens. |
| `GPU_MEMORY_UTILIZATION` | `0.85` | Fraction of total VRAM reserved for weights and KV cache. |
| `ENFORCE_EAGER` | `true` | Save ~1.5 GB VRAM on T4/L4 by disabling CUDA graph capture. |
| `HF_TOKEN` | `null` | Hugging Face token for gated models (Llama, Gemma). |
| `CLOUDFLARE_TUNNEL_ENABLED`| `true` | Set `false` to disable tunnel and run strictly on localhost. |
| `CLOUDFLARE_TUNNEL_TOKEN` | `null` | Leave empty to automatically use Quick Tunnel (`trycloudflare.com`). |
| `DEFAULT_MAX_TOKENS` | `512` | Default max completion tokens. |
| `DEFAULT_TEMPERATURE` | `0.7` | Sampling temperature (0.0 for greedy). |
| `DEFAULT_ENABLE_THINKING` | `true` | Parse `<think>` tags for reasoning models. |
| `GITHUB_TOKEN` | `null` | GitHub Personal Access Token for private repo Colab cloning. |
| `REPO_URL` | `null` | GitHub repository URL to clone in Colab. |

---

## 🛡️ Security & VAPT Audit

The engine has undergone complete end-to-end Vulnerability Assessment and Penetration Testing (VAPT):

1. **Path Traversal & Local File Inclusion**:
   - Strictly validates `model_id` against `..` traversal sequences and restricted system roots (`/etc`, `/root`, `/sys`, `/proc`, `/dev`).
2. **Numeric Boundary Hardening**:
   - `gpu_memory_utilization` enforced between `(0.0, 1.0]`.
   - `max_model_len` enforced between `[1, 131072]`.
   - `temperature`, `top_p`, `repetition_penalty` reject `NaN` and `Inf`.
3. **Information Disclosure Prevention**:
   - Error responses sanitize and redact `HF_TOKEN` and Bearer tokens.
4. **Defensive Response Headers**:
   - Injects `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`.
5. **ReDoS Resilience**:
   - Validated linear performance on deep and malformed thinking tags.

Run the test suite:
```bash
pytest -v
```
*(108 passing unit, integration, and security tests)*
