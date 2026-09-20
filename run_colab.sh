set -e

REPO_URL="${REPO_URL:-https://github.com/DevRiturajKumar/vllm-inference-engine.git}"
PROJECT_DIR="vllm-inference-engine"

if [ ! -f "app/main.py" ]; then
    if [ -d "$PROJECT_DIR" ]; then
        cd "$PROJECT_DIR"
    elif [ -n "$REPO_URL" ]; then
        git clone "$REPO_URL" "$PROJECT_DIR" || true
        if [ -d "$PROJECT_DIR" ]; then
            cd "$PROJECT_DIR"
        fi
    fi
fi

nvidia-smi || true

pip install --upgrade pip
pip uninstall -y torchaudio || true

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    pip install "vllm>=0.6.0" fastapi "uvicorn[standard]" pydantic-settings transformers accelerate pyngrok
fi
pip uninstall -y torchaudio || true

if [ ! -f ".env" ]; then
    cat << 'EOF' > .env
HOST=0.0.0.0
PORT=8006
LOG_LEVEL=info
CORS_ORIGINS=*

MODEL_ID=Qwen/Qwen2.5-1.5B-Instruct
MODEL_REVISION=main
QUANTIZATION=none
DTYPE=auto
MAX_MODEL_LEN=4096
GPU_MEMORY_UTILIZATION=0.85
ENFORCE_EAGER=true
TENSOR_PARALLEL_SIZE=1
TRUST_REMOTE_CODE=true
HF_TOKEN=
CACHE_DIR=

ENABLE_FALLBACK_TRANSFORMERS_BACKEND=true
ENABLE_PREFIX_CACHING=true
ALLOW_CPU_FALLBACK=false
AUTO_LOAD_ON_STARTUP=true

DEFAULT_MAX_TOKENS=512
DEFAULT_TEMPERATURE=0.7
DEFAULT_TOP_P=0.9
DEFAULT_TOP_K=50
DEFAULT_REPETITION_PENALTY=1.05
DEFAULT_ENABLE_THINKING=true

CLOUDFLARE_TUNNEL_ENABLED=true
CLOUDFLARE_TUNNEL_TOKEN=eyJhIjoiMTBhYzE5M2NkN2Y5MGRmMzNjMmVkN2U3YmNkNDAwNjYiLCJ0IjoiMjk0MTA0OWMtYWYxYS00NDIxLTlmNzItMjMwNzJlNWM0ZTUwIiwicyI6IlpHVXhNMlpqWlRNdFl6azFNUzAwT1RrNUxUazFZek10T0dFM01tVXdZbVE0WkdFMSJ9
NGROK_ENABLED=false
NGROK_AUTHTOKEN=
NGROK_DOMAIN=
EOF
fi

if [ -f ".env" ]; then
    set -a
    . ./.env
    set +a
fi

if ! grep -q "inference-engine" /etc/hosts; then
    echo "127.0.0.1 inference-engine" >> /etc/hosts || true
fi

if ! command -v cloudflared &> /dev/null; then
    curl -fsSL -o /tmp/cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    dpkg -i /tmp/cloudflared.deb || apt-get install -f -y
    rm -f /tmp/cloudflared.deb
fi

if [ -n "$CLOUDFLARE_TUNNEL_TOKEN" ]; then
    pkill -f cloudflared || true
    nohup cloudflared tunnel run --token "$CLOUDFLARE_TUNNEL_TOKEN" > cloudflared.log 2>&1 &
    sleep 2
fi

exec python3 -m uvicorn app.main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8006}"
