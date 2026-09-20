#!/usr/bin/env bash
set -e

REPO_URL="${REPO_URL:-}"
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

# Verify GPU
nvidia-smi || true

# Install dependencies
pip install --upgrade pip
pip uninstall -y torchaudio || true

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    pip install "vllm>=0.6.0" fastapi "uvicorn[standard]" pydantic-settings transformers accelerate pyngrok
fi
pip uninstall -y torchaudio || true

# Initialize .env template if not present
if [ ! -f ".env" ]; then
    cat << 'EOF' > .env
HOST=0.0.0.0
PORT=8006
LOG_LEVEL=info
CORS_ORIGINS=*

MODEL_ID=
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
AUTO_LOAD_ON_STARTUP=false

DEFAULT_MAX_TOKENS=512
DEFAULT_TEMPERATURE=0.7
DEFAULT_TOP_P=0.9
DEFAULT_TOP_K=50
DEFAULT_REPETITION_PENALTY=1.05
DEFAULT_ENABLE_THINKING=true

CLOUDFLARE_TUNNEL_ENABLED=true
CLOUDFLARE_TUNNEL_TOKEN=
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

# Process cleanup on script exit
cleanup() {
    pkill -f "cloudflared tunnel" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Cloudflare Tunnel Configuration
if [ "${CLOUDFLARE_TUNNEL_ENABLED:-true}" != "false" ]; then
    if ! command -v cloudflared &> /dev/null; then
        echo "Installing cloudflared binary..."
        curl -fsSL -o /tmp/cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
        dpkg -i /tmp/cloudflared.deb || apt-get install -f -y
        rm -f /tmp/cloudflared.deb
    fi

    pkill -f "cloudflared tunnel" 2>/dev/null || true

    if [ -n "$CLOUDFLARE_TUNNEL_TOKEN" ]; then
        echo "Starting Cloudflare Named Tunnel..."
        nohup cloudflared tunnel run --token "$CLOUDFLARE_TUNNEL_TOKEN" > cloudflared.log 2>&1 &
        sleep 2
    else
        echo "Starting Cloudflare Quick Tunnel (trycloudflare.com) on port ${PORT:-8006}..."
        nohup cloudflared tunnel --url "http://127.0.0.1:${PORT:-8006}" --no-autoupdate > cloudflared.log 2>&1 &
        
        TUNNEL_URL=""
        TIMEOUT=30
        ELAPSED=0
        while [ $ELAPSED -lt $TIMEOUT ]; do
            if [ -f cloudflared.log ]; then
                TUNNEL_URL=$(grep -oE 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' cloudflared.log | grep -v 'https://api\.trycloudflare\.com' | head -n 1 || true)
                if [ -n "$TUNNEL_URL" ]; then
                    break
                fi
            fi
            sleep 1
            ELAPSED=$((ELAPSED + 1))
        done

        if [ -n "$TUNNEL_URL" ]; then
            echo ""
            echo "=================================================================="
            echo " 🌐 Cloudflare Quick Tunnel Live: $TUNNEL_URL"
            echo " 📚 Swagger UI Documentation:    $TUNNEL_URL/docs"
            echo " 💻 Local Endpoint:              http://localhost:${PORT:-8006}"
            echo "=================================================================="
            echo ""
            echo "$TUNNEL_URL" > tunnel_url.txt
        else
            echo "Notice: Cloudflare tunnel started. Check cloudflared.log for live URL."
        fi
    fi
else
    echo "CLOUDFLARE_TUNNEL_ENABLED=false: Serving strictly on localhost (tunnel disabled)."
fi

# Run FastAPI vLLM Engine
exec python3 -m uvicorn app.main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8006}"
