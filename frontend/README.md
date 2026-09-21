# vLLM Studio — Mobile-Responsive Web UI

A modern, high-performance web interface for the **vLLM FastAPI Inference Engine**, built with **React**, **Vite**, **Tailwind CSS**, and **Lucide React**.

This frontend is **100% standalone and decoupled**. You can move this entire `frontend/` folder anywhere (or deploy it to Vercel, Netlify, Cloudflare Pages, S3, or GitHub Pages) and simply point it to your running vLLM FastAPI backend.

---

## 🚀 Key Features

- **📱 Fully Mobile Responsive**:
  - Touch-first design with $\ge 44\text{px}$ touch targets.
  - Slide-in off-canvas drawer on mobile devices with smooth backdrop blur.
  - Sticky bottom chat bar optimized with iOS safe-area insets (`env(safe-area-inset-bottom)`).
- **🌗 Light & Dark Mode Toggler**:
  - Smooth theme switching with Lucide `Sun` and `Moon` icons.
  - Automatic system color scheme detection and persistent `localStorage` saving.
  - Zero Flash of Unstyled Content (FOUC).
- **⚡ Real-Time SSE Token Streaming**:
  - Token-by-token streaming via Server-Sent Events (`/v1/chat/completions`).
  - Stop generation button with immediate `AbortController` cancellation.
- **🧠 DeepSeek R1 & QwQ Reasoning Accordion**:
  - Real-time extraction of `<think>` and `<thinking>` chain-of-thought blocks.
  - Collapsible accordion with thinking timers, live status indicators, and character counts.
- **📊 Live GPU VRAM & Health Monitor**:
  - Live polling of `/health` showing GPU device name (e.g. Tesla T4, NVIDIA L4, A100).
  - Color-coded VRAM utilization progress bar (Green $\le 70\%$, Amber $70-85\%$, Red $> 85\%$).
- **🎛️ Dynamic Model Lifecycle Manager**:
  - Interactive modal to hot-swap or load models on the fly via `/admin/load-model`.
  - Presets for Qwen 2.5, DeepSeek R1 Distill, Llama 3.2, and AWQ 4-bit models.
  - Complete memory eviction and VRAM reclamation via `/admin/unload-model`.
- **🌐 Configurable API Endpoint**:
  - Supports `http://localhost:8006` or public Cloudflare Tunnel URLs (`https://<subdomain>.trycloudflare.com`).
  - Built-in latency ping test.

---

## 🛠️ Getting Started

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Start Development Server
```bash
npm run dev
```
The application will launch at `http://localhost:3000`.

### 3. Build for Production
```bash
npm run build
```
This generates the optimized static assets in `frontend/dist/`.

---

## 🚢 Deployment Anywhere

Because the frontend is a standalone Single Page Application (SPA), you can host `frontend/dist/` or deploy `frontend/` to:
- **Vercel**: `vercel`
- **Netlify**: `netlify deploy --dir=dist`
- **Cloudflare Pages**: Link repo and set build output to `dist`
- **Static Nginx / Docker**: Copy `dist/` into `/usr/share/nginx/html`

Once deployed, click the **Settings (gear)** icon in the top navbar to set your vLLM backend URL.
