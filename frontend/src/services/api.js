/**
 * Service for interacting with the vLLM FastAPI Inference Engine API
 */

export function cleanBaseUrl(url) {
  if (!url) return '';
  return url
    .trim()
    .replace(/\/+$/, '')
    .replace(/\/(docs|redoc)(#.*)?$/i, '')
    .replace(/\/+$/, '');
}

/**
 * Fetch health status and live GPU/VRAM statistics
 */
export async function fetchHealth(baseUrl) {
  const url = `${cleanBaseUrl(baseUrl)}/health`;
  const res = await fetch(url, {
    headers: { 'Accept': 'application/json' },
  });
  if (!res.ok) {
    throw new Error(`Health check failed (${res.status} ${res.statusText})`);
  }
  return await res.json();
}

/**
 * Fetch list of currently active / loaded models
 */
export async function fetchModels(baseUrl) {
  const url = `${cleanBaseUrl(baseUrl)}/v1/models`;
  const res = await fetch(url, {
    headers: { 'Accept': 'application/json' },
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch models (${res.status} ${res.statusText})`);
  }
  return await res.json();
}

/**
 * Fetch active engine config
 */
export async function fetchCurrentModel(baseUrl) {
  const url = `${cleanBaseUrl(baseUrl)}/admin/current-model`;
  const res = await fetch(url, {
    headers: { 'Accept': 'application/json' },
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch current model (${res.status})`);
  }
  return await res.json();
}

/**
 * Load or hot-swap a model
 */
export async function loadModel(baseUrl, payload) {
  const url = `${cleanBaseUrl(baseUrl)}/admin/load-model`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Model load failed with status ${res.status}`);
  }
  return await res.json();
}

/**
 * Unload active model and reclaim GPU VRAM
 */
export async function unloadModel(baseUrl) {
  const url = `${cleanBaseUrl(baseUrl)}/admin/unload-model`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Accept': 'application/json' },
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Model unload failed with status ${res.status}`);
  }
  return await res.json();
}

/**
 * Stream chat completions using SSE
 */
export async function streamChatCompletion(baseUrl, requestPayload, { onChunk, onDone, onError, signal }) {
  const url = `${cleanBaseUrl(baseUrl)}/v1/chat/completions`;
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify({ ...requestPayload, stream: true }),
      signal,
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorMsg = `Server returned ${response.status} ${response.statusText}`;
      try {
        const parsed = JSON.parse(errorText);
        if (parsed.detail) errorMsg = parsed.detail;
        if (parsed.error?.message) errorMsg = parsed.error.message;
      } catch (e) {
        if (errorText) errorMsg = errorText;
      }
      throw new Error(errorMsg);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith(':')) continue; // comments/ping

        if (trimmed === 'data: [DONE]') {
          if (onDone) onDone();
          return;
        }

        if (trimmed.startsWith('data: ')) {
          const jsonStr = trimmed.slice(6);
          try {
            const data = JSON.parse(jsonStr);
            if (data.error) {
              throw new Error(data.error.message || 'Stream error occurred');
            }
            if (onChunk) onChunk(data);
          } catch (err) {
            console.warn('Failed to parse SSE chunk:', jsonStr, err);
          }
        }
      }
    }

    if (onDone) onDone();
  } catch (err) {
    if (err.name === 'AbortError') {
      if (onDone) onDone({ aborted: true });
      return;
    }
    if (onError) onError(err);
    else throw err;
  }
}
