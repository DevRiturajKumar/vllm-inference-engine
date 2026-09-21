#!/usr/bin/env bash
set -e

# Navigate to the script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PROJECT_DIR="vllm-inference-engine"

# Load .env if present before reading repository settings
if [ -f ".env" ]; then
    set -a
    . ./.env
    set +a
elif [ -f "../.env" ]; then
    set -a
    . ../.env
    set +a
elif [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    . "./$PROJECT_DIR/.env"
    set +a
fi

GITHUB_TOKEN="${GITHUB_TOKEN:-}"
REPO_URL="${REPO_URL:-}"

# Verify repository files exist or clone if needed
if [ ! -f "app/main.py" ]; then
    if [ -d "$PROJECT_DIR" ] && [ -f "$PROJECT_DIR/app/main.py" ]; then
        cd "$PROJECT_DIR"
    elif [ -n "$REPO_URL" ]; then
        if [ -n "$GITHUB_TOKEN" ]; then
            CLEAN_REPO="${REPO_URL#*@}"
            CLEAN_REPO="${CLEAN_REPO#https://}"
            CLEAN_REPO="${CLEAN_REPO#http://}"
            AUTH_REPO_URL="https://${GITHUB_TOKEN}@${CLEAN_REPO}"
            echo "Cloning private repository using GITHUB_TOKEN from .env..."
            git clone "$AUTH_REPO_URL" "$PROJECT_DIR" || true
        else
            echo "Cloning repository..."
            git clone "$REPO_URL" "$PROJECT_DIR" || true
        fi
        if [ -d "$PROJECT_DIR" ] && [ -f "$PROJECT_DIR/app/main.py" ]; then
            # Ensure top-level .env from Colab always propagates into cloned directory
            if [ -f ".env" ]; then
                cp -f .env "$PROJECT_DIR/.env"
            fi
            cd "$PROJECT_DIR"
        fi
    fi
fi

# Re-source .env if present in the target directory
if [ -f ".env" ]; then
    set -a
    . ./.env
    set +a
fi

# Strict check for required application files
if [ ! -f "app/main.py" ]; then
    echo ""
    echo "========================================================================"
    echo " [ERROR] 'app/main.py' could not be found in $(pwd)!"
    echo "========================================================================"
    echo " If your repository is PRIVATE, add GITHUB_TOKEN and REPO_URL to .env:"
    echo ""
    echo "   GITHUB_TOKEN=ghp_yourPersonalAccessToken"
    echo "   REPO_URL=https://github.com/your-username/your-repo.git"
    echo ""
    echo " Or export them directly before running:"
    echo "   export GITHUB_TOKEN=\"ghp_xxx\""
    echo "   export REPO_URL=\"https://github.com/your-username/your-repo.git\""
    echo "   bash run_colab.sh"
    echo ""
    echo " Alternatively, zip and upload this directory directly to Colab:"
    echo "   !unzip -q vllm-inference-engine.zip -d vllm-inference-engine"
    echo "   %cd vllm-inference-engine"
    echo "   !sed -i 's/\\r$//' run_colab.sh && bash run_colab.sh"
    echo "========================================================================"
    echo ""
    exit 1
fi

# Ensure Python imports always find 'app' from project root
export PYTHONPATH="$(pwd):${PYTHONPATH:-}"

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
DEFAULT_ENABLE_THINKING=false

CLOUDFLARE_TUNNEL_ENABLED=true
CLOUDFLARE_TUNNEL_TOKEN=
NGROK_ENABLED=false
NGROK_AUTHTOKEN=
NGROK_DOMAIN=

# GitHub Private Repository Settings (Optional - for Colab bootstrap)
GITHUB_TOKEN=
REPO_URL=
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

# Ensure cloudflared binary is installed if tunnel is enabled
if [ "${CLOUDFLARE_TUNNEL_ENABLED:-true}" != "false" ]; then
    if ! command -v cloudflared &> /dev/null; then
        echo "Installing cloudflared binary..."
        curl -fsSL -o /tmp/cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
        dpkg -i /tmp/cloudflared.deb || apt-get install -f -y
        rm -f /tmp/cloudflared.deb
    fi
    pkill -f "cloudflared tunnel" 2>/dev/null || true
else
    echo "CLOUDFLARE_TUNNEL_ENABLED=false: Serving strictly on localhost (tunnel disabled)."
fi

# Run FastAPI vLLM Engine (manages the single live tunnel and outputs the active URL)
exec python3 -m uvicorn app.main:app --app-dir "$(pwd)" --host "${HOST:-0.0.0.0}" --port "${PORT:-8006}"
