/**
 * Helper to display clean human-readable model names
 */
export function formatModelName(modelId) {
  if (!modelId) return 'vLLM Assistant';
  
  // Strip organization prefix e.g. "deepseek-ai/", "Qwen/", "meta-llama/"
  const cleanId = modelId.split('/').pop() || modelId;

  // Custom mapping for well-known models
  const map = {
    'DeepSeek-R1-Distill-Qwen-1.5B': 'DeepSeek R1 Distill 1.5B',
    'DeepSeek-R1-Distill-Qwen-7B': 'DeepSeek R1 Distill 7B',
    'DeepSeek-R1-Distill-Llama-8B': 'DeepSeek R1 Distill 8B',
    'Qwen2.5-1.5B-Instruct': 'Qwen 2.5 1.5B',
    'Qwen2.5-0.5B-Instruct': 'Qwen 2.5 0.5B',
    'Qwen2.5-3B-Instruct': 'Qwen 2.5 3B',
    'Qwen2.5-7B-Instruct': 'Qwen 2.5 7B',
    'Qwen2.5-7B-Instruct-AWQ': 'Qwen 2.5 7B AWQ',
    'Qwen2.5-Coder-1.5B-Instruct': 'Qwen 2.5 Coder 1.5B',
    'Qwen2.5-Coder-7B-Instruct': 'Qwen 2.5 Coder 7B',
    'Llama-3.2-1B-Instruct': 'Llama 3.2 1B',
    'Llama-3.2-3B-Instruct': 'Llama 3.2 3B',
    'Meta-Llama-3.1-8B-Instruct': 'Llama 3.1 8B',
  };

  if (map[cleanId]) return map[cleanId];

  // Generic cleanup: replace dashes with spaces, clean "-Instruct"
  return cleanId
    .replace(/-Instruct$/i, '')
    .replace(/[-_]/g, ' ');
}

/**
 * Extracts any unparsed <think>...</think> or ...</think> from raw content text
 */
export function extractThinkingFromContent(rawText) {
  if (!rawText) return { reasoning: '', content: '' };

  // 1. Full <think>...</think> or <thinking>...</thinking>
  const fullMatch = rawText.match(/<(?:think|thinking)>([\s\S]*?)<\/(?:think|thinking)>/i);
  if (fullMatch) {
    const reasoning = fullMatch[1].trim();
    const content = (rawText.slice(0, fullMatch.index) + rawText.slice(fullMatch.index + fullMatch[0].length)).trim();
    return { reasoning, content };
  }

  // 2. Only closing </think> or </thinking> (when prompt already injected <think>)
  const closeMatch = rawText.match(/([\s\S]*?)<\/(?:think|thinking)>/i);
  if (closeMatch) {
    const reasoning = closeMatch[1].replace(/^<(?:think|thinking)>/i, '').trim();
    const content = rawText.slice(closeMatch.index + closeMatch[0].length).trim();
    return { reasoning, content };
  }

  // 3. Open <think>... (streaming without closing yet)
  const openMatch = rawText.match(/<(?:think|thinking)>([\s\S]*)/i);
  if (openMatch) {
    const reasoning = openMatch[1].trim();
    const content = rawText.slice(0, openMatch.index).trim();
    return { reasoning, content, isOpen: true };
  }

  return { reasoning: '', content: rawText };
}

/**
 * Checks whether a model ID is a reasoning/thinking model (DeepSeek-R1, QwQ, etc.)
 */
export function isReasoningModel(modelId) {
  if (!modelId) return false;
  const lower = modelId.toLowerCase();
  const patterns = ['deepseek-r1', 'r1-distill', 'qwq', 'thinking', 'reasoner', 'qwen3'];
  return patterns.some(p => lower.includes(p));
}
