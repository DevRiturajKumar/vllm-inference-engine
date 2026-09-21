import React, { useState } from 'react';
import { 
  X, 
  Layers, 
  Cpu, 
  Database, 
  Key, 
  Check, 
  AlertCircle, 
  Loader2, 
  Sparkles,
  Sliders,
  Power,
  Brain,
  Lock,
  ChevronDown
} from 'lucide-react';
import { loadModel, unloadModel, fetchHealth } from '../services/api';
import { useSettings } from '../context/SettingsContext';

export const CATEGORIZED_MODELS = [
  {
    category: "Qwen 2.5 (General Purpose)",
    models: [
      { id: "Qwen/Qwen2.5-0.5B-Instruct", name: "Qwen 2.5 0.5B Instruct", quant: "none", maxLen: 32768, vram: "~3.5 GB", tier: "T4 / L4 / A100" },
      { id: "Qwen/Qwen2.5-0.5B-Instruct-AWQ", name: "Qwen 2.5 0.5B AWQ (4-bit)", quant: "awq", maxLen: 32768, vram: "~2.5 GB", tier: "T4 / L4 / A100" },
      { id: "Qwen/Qwen2.5-1.5B-Instruct", name: "Qwen 2.5 1.5B Instruct", quant: "none", maxLen: 32768, vram: "~5.8 GB", tier: "T4 / L4 / A100" },
      { id: "Qwen/Qwen2.5-1.5B-Instruct-AWQ", name: "Qwen 2.5 1.5B AWQ (4-bit)", quant: "awq", maxLen: 32768, vram: "~3.8 GB", tier: "T4 / L4 / A100" },
      { id: "Qwen/Qwen2.5-3B-Instruct", name: "Qwen 2.5 3B Instruct", quant: "none", maxLen: 16384, vram: "~9.5 GB", tier: "T4 / L4 / A100" },
      { id: "Qwen/Qwen2.5-3B-Instruct-AWQ", name: "Qwen 2.5 3B AWQ (4-bit)", quant: "awq", maxLen: 32768, vram: "~5.5 GB", tier: "T4 / L4 / A100" },
      { id: "Qwen/Qwen2.5-7B-Instruct", name: "Qwen 2.5 7B Instruct", quant: "none", maxLen: 16384, vram: "~19.5 GB", tier: "L4 / A100 (OOM on T4)" },
      { id: "Qwen/Qwen2.5-7B-Instruct-AWQ", name: "Qwen 2.5 7B AWQ (4-bit)", quant: "awq", maxLen: 8192, vram: "~7.5 GB", tier: "T4 / L4 / A100" },
      { id: "Qwen/Qwen2.5-14B-Instruct", name: "Qwen 2.5 14B Instruct", quant: "none", maxLen: 16384, vram: "~35.0 GB", tier: "A100-40GB / 80GB" },
      { id: "Qwen/Qwen2.5-14B-Instruct-AWQ", name: "Qwen 2.5 14B AWQ (4-bit)", quant: "awq", maxLen: 8192, vram: "~12.5 GB", tier: "T4 (eager) / L4 / A100" },
      { id: "Qwen/Qwen2.5-32B-Instruct", name: "Qwen 2.5 32B Instruct", quant: "none", maxLen: 16384, vram: "~74.0 GB", tier: "A100-80GB" },
      { id: "Qwen/Qwen2.5-32B-Instruct-AWQ", name: "Qwen 2.5 32B AWQ (4-bit)", quant: "awq", maxLen: 4096, vram: "~22.0 GB", tier: "L4 (eager) / A100" },
      { id: "Qwen/Qwen2.5-72B-Instruct-AWQ", name: "Qwen 2.5 72B AWQ (4-bit)", quant: "awq", maxLen: 8192, vram: "~52.0 GB", tier: "A100-80GB" },
    ]
  },
  {
    category: "Qwen 2.5 Coder (Programming)",
    models: [
      { id: "Qwen/Qwen2.5-Coder-1.5B-Instruct", name: "Qwen 2.5 Coder 1.5B Instruct", quant: "none", maxLen: 32768, vram: "~5.8 GB", tier: "T4 / L4 / A100" },
      { id: "Qwen/Qwen2.5-Coder-7B-Instruct-AWQ", name: "Qwen 2.5 Coder 7B AWQ (4-bit)", quant: "awq", maxLen: 8192, vram: "~7.5 GB", tier: "T4 / L4 / A100" },
      { id: "Qwen/Qwen2.5-Coder-14B-Instruct-AWQ", name: "Qwen 2.5 Coder 14B AWQ (4-bit)", quant: "awq", maxLen: 8192, vram: "~12.5 GB", tier: "T4 (eager) / L4 / A100" },
      { id: "Qwen/Qwen2.5-Coder-32B-Instruct-AWQ", name: "Qwen 2.5 Coder 32B AWQ (4-bit)", quant: "awq", maxLen: 4096, vram: "~22.0 GB", tier: "L4 (eager) / A100" },
    ]
  },
  {
    category: "DeepSeek R1 & Reasoning (Chain of Thought)",
    models: [
      { id: "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B", name: "DeepSeek R1 Distill Qwen 1.5B", quant: "none", maxLen: 32768, vram: "~5.8 GB", tier: "T4 / L4 / A100", isThinking: true },
      { id: "casperhansen/deepseek-r1-distill-qwen-1.5b-awq", name: "DeepSeek R1 Distill Qwen 1.5B AWQ", quant: "awq", maxLen: 32768, vram: "~3.8 GB", tier: "T4 / L4 / A100", isThinking: true },
      { id: "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B", name: "DeepSeek R1 Distill Qwen 7B", quant: "none", maxLen: 16384, vram: "~19.5 GB", tier: "L4 / A100", isThinking: true },
      { id: "casperhansen/deepseek-r1-distill-qwen-7b-awq", name: "DeepSeek R1 Distill Qwen 7B AWQ", quant: "awq", maxLen: 8192, vram: "~7.5 GB", tier: "T4 / L4 / A100", isThinking: true },
      { id: "deepseek-ai/DeepSeek-R1-Distill-Llama-8B", name: "DeepSeek R1 Distill Llama 8B", quant: "none", maxLen: 16384, vram: "~20.0 GB", tier: "L4 / A100", isThinking: true },
      { id: "casperhansen/deepseek-r1-distill-llama-8b-awq", name: "DeepSeek R1 Distill Llama 8B AWQ", quant: "awq", maxLen: 8192, vram: "~8.0 GB", tier: "T4 / L4 / A100", isThinking: true },
      { id: "casperhansen/deepseek-r1-distill-qwen-14b-awq", name: "DeepSeek R1 Distill Qwen 14B AWQ", quant: "awq", maxLen: 8192, vram: "~12.5 GB", tier: "T4 (eager) / L4 / A100", isThinking: true },
      { id: "casperhansen/deepseek-r1-distill-qwen-32b-awq", name: "DeepSeek R1 Distill Qwen 32B AWQ", quant: "awq", maxLen: 4096, vram: "~22.0 GB", tier: "L4 (eager) / A100", isThinking: true },
      { id: "casperhansen/deepseek-r1-distill-llama-70b-awq", name: "DeepSeek R1 Distill Llama 70B AWQ", quant: "awq", maxLen: 8192, vram: "~51.0 GB", tier: "A100-80GB", isThinking: true },
    ]
  },
  {
    category: "Meta Llama 3.3 / 3.2 / 3.1",
    models: [
      { id: "meta-llama/Llama-3.2-1B-Instruct", name: "Llama 3.2 1B Instruct", quant: "none", maxLen: 32768, vram: "~5.0 GB", tier: "T4 / L4 / A100", gated: true },
      { id: "casperhansen/llama-3.2-1b-instruct-awq", name: "Llama 3.2 1B AWQ (Ungated)", quant: "awq", maxLen: 32768, vram: "~3.5 GB", tier: "T4 / L4 / A100" },
      { id: "meta-llama/Llama-3.2-3B-Instruct", name: "Llama 3.2 3B Instruct", quant: "none", maxLen: 16384, vram: "~9.8 GB", tier: "T4 / L4 / A100", gated: true },
      { id: "casperhansen/llama-3.2-3b-instruct-awq", name: "Llama 3.2 3B AWQ (Ungated)", quant: "awq", maxLen: 32768, vram: "~5.8 GB", tier: "T4 / L4 / A100" },
      { id: "meta-llama/Meta-Llama-3.1-8B-Instruct", name: "Llama 3.1 8B Instruct", quant: "none", maxLen: 8192, vram: "~20.2 GB", tier: "L4 / A100", gated: true },
      { id: "hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4", name: "Llama 3.1 8B AWQ (Ungated)", quant: "awq", maxLen: 8192, vram: "~8.2 GB", tier: "T4 / L4 / A100" },
      { id: "hugging-quants/Meta-Llama-3.1-70B-Instruct-AWQ-INT4", name: "Llama 3.1 70B AWQ (Ungated)", quant: "awq", maxLen: 8192, vram: "~51.0 GB", tier: "A100-80GB" },
      { id: "casperhansen/llama-3.3-70b-instruct-awq", name: "Llama 3.3 70B AWQ (Ungated)", quant: "awq", maxLen: 8192, vram: "~51.0 GB", tier: "A100-80GB" },
    ]
  },
  {
    category: "Google Gemma 2 & Gemma 3",
    models: [
      { id: "google/gemma-2-2b-it", name: "Gemma 2 2B Instruct", quant: "none", maxLen: 8192, vram: "~8.0 GB", tier: "T4 / L4 / A100", gated: true },
      { id: "TechxGenus/gemma-2b-it-AWQ", name: "Gemma 1 2B AWQ (Ungated)", quant: "awq", maxLen: 8192, vram: "~4.5 GB", tier: "T4 / L4 / A100" },
      { id: "google/gemma-2-9b-it", name: "Gemma 2 9B Instruct", quant: "none", maxLen: 4096, vram: "~21.5 GB", tier: "L4 / A100", gated: true },
      { id: "solidrust/gemma-2-9b-it-AWQ", name: "Gemma 2 9B AWQ (Ungated)", quant: "awq", maxLen: 4096, vram: "~11.0 GB", tier: "T4 (eager) / L4 / A100" },
      { id: "mbley/google-gemma-2-27b-it-AWQ", name: "Gemma 2 27B AWQ (Ungated)", quant: "awq", maxLen: 4096, vram: "~21.5 GB", tier: "L4 (eager) / A100" },
      { id: "google/gemma-3-1b-it", name: "Gemma 3 1B Instruct", quant: "none", maxLen: 32768, vram: "~5.2 GB", tier: "T4 / L4 / A100", gated: true },
      { id: "google/gemma-3-4b-it", name: "Gemma 3 4B Instruct (Vision)", quant: "none", maxLen: 16384, vram: "~13.5 GB", tier: "T4 (eager) / L4 / A100", gated: true, multimodal: true },
    ]
  },
  {
    category: "Mistral & Mixtral",
    models: [
      { id: "mistralai/Mistral-7B-Instruct-v0.3", name: "Mistral 7B v0.3 Instruct", quant: "none", maxLen: 8192, vram: "~19.0 GB", tier: "L4 / A100" },
      { id: "TechxGenus/Mistral-7B-Instruct-v0.3-AWQ", name: "Mistral 7B v0.3 AWQ (4-bit)", quant: "awq", maxLen: 8192, vram: "~7.2 GB", tier: "T4 / L4 / A100" },
      { id: "TheBloke/Mixtral-8x7B-Instruct-v0.1-AWQ", name: "Mixtral 8x7B AWQ", quant: "awq", maxLen: 8192, vram: "~34.0 GB", tier: "A100-40GB / 80GB" },
      { id: "mistralai/Ministral-3-3B-Instruct-2512", name: "Ministral 3 3B Instruct (FP8)", quant: "fp8", maxLen: 16384, vram: "~6.5 GB", tier: "T4 (eager) / L4 / A100" },
      { id: "mistralai/Ministral-8B-Instruct-2410", name: "Ministral 8B Instruct", quant: "none", maxLen: 8192, vram: "~20.5 GB", tier: "L4 / A100" },
    ]
  },
  {
    category: "Microsoft Phi 3.5 & Phi 4",
    models: [
      { id: "microsoft/Phi-3.5-mini-instruct", name: "Phi-3.5-mini Instruct", quant: "none", maxLen: 8192, vram: "~11.8 GB", tier: "T4 (eager) / L4 / A100" },
      { id: "thesven/Phi-3.5-mini-instruct-awq", name: "Phi-3.5-mini AWQ (4-bit)", quant: "awq", maxLen: 16384, vram: "~6.5 GB", tier: "T4 / L4 / A100" },
      { id: "microsoft/phi-4", name: "Phi-4 (14B)", quant: "none", maxLen: 8192, vram: "~34.5 GB", tier: "A100-40GB / 80GB" },
      { id: "microsoft/Phi-4-mini-instruct", name: "Phi-4-mini Instruct", quant: "none", maxLen: 8192, vram: "~11.8 GB", tier: "T4 (eager) / L4 / A100" },
    ]
  }
];

export function ModelManagerModal({ 
  isOpen, 
  onClose, 
  currentModel, 
  onModelChanged 
}) {
  const { settings } = useSettings();

  const [modelId, setModelId] = useState(currentModel || 'Qwen/Qwen2.5-1.5B-Instruct');
  const [quantization, setQuantization] = useState('none');
  const [maxModelLen, setMaxModelLen] = useState(4096);
  const [gpuMemoryUtilization, setGpuMemoryUtilization] = useState(0.85);
  const [enforceEager, setEnforceEager] = useState(true);
  const [hfToken, setHfToken] = useState(() => {
    return (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_HF_TOKEN) || '';
  });

  const [selectedMeta, setSelectedMeta] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  if (!isOpen) return null;

  const handleSelectFromDropdown = (e) => {
    const selectedId = e.target.value;
    if (!selectedId) return;

    // Find in categorized models
    let found = null;
    for (const group of CATEGORIZED_MODELS) {
      const match = group.models.find(m => m.id === selectedId);
      if (match) {
        found = match;
        break;
      }
    }

    if (found) {
      setModelId(found.id);
      setQuantization(found.quant);
      setMaxModelLen(found.maxLen);
      setSelectedMeta(found);
    } else {
      setSelectedMeta(null);
    }
  };

  const handleLoad = async (e) => {
    e.preventDefault();
    if (!modelId.trim() || isLoading) return;

    setIsLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    setLoadingStatus("Connecting to inference engine...");

    const targetModelId = modelId.trim();
    try {
      const payload = {
        model_id: targetModelId,
        quantization: quantization === 'none' ? null : quantization,
        dtype: 'auto',
        max_model_len: Number(maxModelLen),
        gpu_memory_utilization: Number(gpuMemoryUtilization),
        enforce_eager: Boolean(enforceEager),
        hf_token: hfToken.trim() || null,
      };

      setLoadingStatus("Downloading weights & initializing VRAM in Colab...");

      try {
        await loadModel(settings.baseUrl, payload);
        setSuccessMsg(`Model successfully loaded: ${targetModelId}`);
        if (onModelChanged) onModelChanged();
        setTimeout(() => {
          onClose();
        }, 1200);
      } catch (loadErr) {
        // If Cloudflare or network proxy timed out with "Failed to fetch" or 524/504,
        // the server is usually still downloading & initializing in the background.
        const isNetworkOrTimeout = !loadErr.message || 
          loadErr.message.includes('fetch') || 
          loadErr.message.includes('524') || 
          loadErr.message.includes('504') || 
          loadErr.message.includes('NetworkError');

        if (isNetworkOrTimeout) {
          setLoadingStatus("Download in progress in Colab. Waiting for VRAM allocation...");
          let loaded = false;
          // Poll /health every 3 seconds for up to 2.5 minutes (50 attempts)
          for (let attempt = 1; attempt <= 50; attempt++) {
            await new Promise((r) => setTimeout(r, 3000));
            try {
              const h = await fetchHealth(settings.baseUrl);
              if (h.status === 'OK' && h.loaded_model === targetModelId) {
                loaded = true;
                break;
              } else if (h.status === 'LOADING') {
                setLoadingStatus(`Downloading weights from Hugging Face & allocating VRAM... (${attempt * 3}s)`);
              }
            } catch (pollErr) {
              // Server may be briefly saturated downloading large safetensor chunks
            }
          }

          if (loaded) {
            setSuccessMsg(`Model successfully loaded: ${targetModelId}`);
            if (onModelChanged) onModelChanged();
            setTimeout(() => {
              onClose();
            }, 1200);
          } else {
            throw loadErr;
          }
        } else {
          throw loadErr;
        }
      }
    } catch (err) {
      setErrorMsg(err.message || 'Failed to load model.');
    } finally {
      setIsLoading(false);
      setLoadingStatus(null);
    }
  };

  const handleUnload = async () => {
    if (isLoading) return;
    setIsLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      await unloadModel(settings.baseUrl);
      setSuccessMsg('Model unloaded and VRAM completely freed.');
      if (onModelChanged) onModelChanged();
      setTimeout(() => {
        onClose();
      }, 1200);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to unload model.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 animate-fade-in">
      {/* Backdrop (backdrop click disabled to prevent accidental dismissal during load or configuration) */}
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm" 
      />

      {/* Modal Dialog */}
      <div className="relative w-full max-w-xl bg-white dark:bg-[#0f172a] rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl overflow-hidden z-10 max-h-[90vh] flex flex-col">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200/80 dark:border-slate-800/80 flex items-center justify-between flex-shrink-0 bg-white dark:bg-[#0f172a]">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-brand-500/10 text-brand-500">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Model Lifecycle Manager
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Hot-swap or load models dynamically in GPU VRAM
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            type="button"
            className="p-2 rounded-xl text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 min-h-[44px] min-w-[44px] flex items-center justify-center"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form wrapping scrollable body and pinned footer */}
        <form onSubmit={handleLoad} className="flex-1 flex flex-col overflow-hidden min-h-0">
          
          {/* Scrollable Modal Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-5 text-slate-800 dark:text-slate-200">
            
            {/* Status Alerts */}
            {isLoading && (
              <div className="flex items-center space-x-3 p-4 rounded-2xl bg-brand-500/10 border border-brand-500/20 text-xs text-brand-700 dark:text-brand-300 animate-pulse">
                <Loader2 className="w-5 h-5 animate-spin flex-shrink-0 text-brand-500" />
                <div>
                  <div className="font-semibold text-slate-800 dark:text-slate-100">
                    Loading Model in Colab
                  </div>
                  <div className="text-[11px] text-slate-600 dark:text-slate-300 mt-0.5">
                    {loadingStatus || "Downloading weights from Hugging Face & allocating VRAM..."}
                  </div>
                </div>
              </div>
            )}

            {errorMsg && (
              <div className="flex items-start space-x-2.5 p-3.5 rounded-2xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-xs text-red-600 dark:text-red-400">
                <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <span>{errorMsg}</span>
              </div>
            )}

            {successMsg && (
              <div className="flex items-center space-x-2.5 p-3.5 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900/60 text-xs text-emerald-600 dark:text-emerald-400">
                <Check className="w-4 h-4 flex-shrink-0" />
                <span>{successMsg}</span>
              </div>
            )}

            {/* Categorized Model Selector Dropdown */}
            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                Supported Model Catalog (Categorized Dropdown)
              </label>
              <div className="relative">
                <select
                  onChange={handleSelectFromDropdown}
                  defaultValue=""
                  className="w-full px-3.5 py-3 text-xs rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500/40 cursor-pointer appearance-none pr-9 font-medium"
                >
                  <option value="" disabled>
                    -- Select a Supported Model from Catalog --
                  </option>
                  {CATEGORIZED_MODELS.map((group, gIdx) => (
                    <optgroup key={gIdx} label={group.category} className="font-semibold text-brand-600 dark:text-brand-400 bg-white dark:bg-slate-900">
                      {group.models.map((m) => (
                        <option 
                          key={m.id} 
                          value={m.id}
                          className="text-slate-800 dark:text-slate-200 font-normal py-1"
                        >
                          {m.name} [{m.vram}]
                        </option>
                      ))}
                    </optgroup>
                  ))}
                </select>
                <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none text-slate-400">
                  <ChevronDown className="w-4 h-4" />
                </div>
              </div>

              {/* Selected Model Details & Badges */}
              {selectedMeta && (
                <div className="flex flex-wrap items-center gap-1.5 pt-1 text-[11px]">
                  <span className="px-2 py-0.5 rounded-md bg-brand-500/10 text-brand-600 dark:text-brand-400 font-medium border border-brand-500/20">
                    {selectedMeta.vram}
                  </span>
                  <span className="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-medium border border-slate-200 dark:border-slate-700">
                    {selectedMeta.tier}
                  </span>
                  {selectedMeta.isThinking && (
                    <span className="px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-600 dark:text-amber-400 font-medium border border-amber-500/20 flex items-center gap-1">
                      <Brain className="w-3 h-3" /> CoT Reasoning
                    </span>
                  )}
                  {selectedMeta.gated && (
                    <span className="px-2 py-0.5 rounded-md bg-purple-500/10 text-purple-600 dark:text-purple-400 font-medium border border-purple-500/20 flex items-center gap-1">
                      <Lock className="w-3 h-3" /> Requires HF Token
                    </span>
                  )}
                  {selectedMeta.multimodal && (
                    <span className="px-2 py-0.5 rounded-md bg-sky-500/10 text-sky-600 dark:text-sky-400 font-medium border border-sky-500/20 flex items-center gap-1">
                      <Sparkles className="w-3 h-3" /> Vision / Multimodal
                    </span>
                  )}
                </div>
              )}
            </div>

            {/* Model ID Input (Editable / Custom) */}
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Hugging Face Model ID or Local Path
              </label>
              <div className="relative">
                <input
                  type="text"
                  required
                  value={modelId}
                  onChange={(e) => {
                    setModelId(e.target.value);
                    setSelectedMeta(null);
                  }}
                  placeholder="e.g. Qwen/Qwen2.5-1.5B-Instruct"
                  className="w-full px-3.5 py-2.5 text-xs font-mono rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500/40"
                />
              </div>
              <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-1">
                Select from dropdown above or paste any custom Hugging Face model repository.
              </p>
            </div>

            {/* Quantization & Max Model Len */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Quantization
                </label>
                <select
                  value={quantization}
                  onChange={(e) => setQuantization(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500/40"
                >
                  <option value="none">None (Full Precision FP16/BF16)</option>
                  <option value="awq">AWQ (4-bit)</option>
                  <option value="gptq">GPTQ (4-bit)</option>
                  <option value="fp8">FP8 (8-bit)</option>
                  <option value="bitsandbytes">BitsAndBytes (8-bit / 4-bit)</option>
                  <option value="squeezellm">SqueezeLLM</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Max Model Length
                </label>
                <input
                  type="number"
                  min="512"
                  max="131072"
                  step="512"
                  value={maxModelLen}
                  onChange={(e) => setMaxModelLen(e.target.value)}
                  className="w-full px-3 py-2 text-xs font-mono rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500/40"
                />
              </div>
            </div>

            {/* GPU Memory Utilization */}
            <div>
              <div className="flex justify-between items-center text-xs mb-1">
                <span className="text-slate-700 dark:text-slate-300 font-medium">
                  GPU Memory Utilization
                </span>
                <span className="font-mono font-semibold text-brand-600 dark:text-brand-400">
                  {Math.round(gpuMemoryUtilization * 100)}%
                </span>
              </div>
              <input
                type="range"
                min="0.2"
                max="0.95"
                step="0.05"
                value={gpuMemoryUtilization}
                onChange={(e) => setGpuMemoryUtilization(parseFloat(e.target.value))}
                className="w-full accent-brand-500 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg cursor-pointer"
              />
            </div>

            {/* Enforce Eager Toggle */}
            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
              <div>
                <span className="text-xs font-medium text-slate-800 dark:text-slate-200 block">
                  Enforce Eager Mode
                </span>
                <span className="text-[11px] text-slate-500 dark:text-slate-400 block">
                  Disables CUDA graphs to save ~1.5 GB VRAM on Colab T4
                </span>
              </div>
              <input
                type="checkbox"
                checked={enforceEager}
                onChange={(e) => setEnforceEager(e.target.checked)}
                className="w-4 h-4 text-brand-600 rounded focus:ring-brand-500 accent-brand-500 cursor-pointer"
              />
            </div>

            {/* Hugging Face Token */}
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Hugging Face Token (Required for Meta Llama & Google Gemma)
              </label>
              <input
                type="password"
                value={hfToken}
                onChange={(e) => setHfToken(e.target.value)}
                placeholder="hf_..."
                className="w-full px-3.5 py-2.5 text-xs font-mono rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500/40"
              />
            </div>

          </div>

          {/* Pinned Action Footer (always visible regardless of scroll position) */}
          <div className="px-6 py-4 border-t border-slate-200/80 dark:border-slate-800/80 bg-slate-50/90 dark:bg-[#0f172a]/95 backdrop-blur-sm flex items-center gap-3 flex-shrink-0 z-10">
            <button
              type="submit"
              disabled={isLoading}
              className="flex-1 py-3 px-4 rounded-xl bg-brand-500 hover:bg-brand-600 disabled:opacity-50 text-white text-xs font-semibold shadow-lg shadow-brand-500/25 transition-all flex items-center justify-center gap-2 min-h-[44px]"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Loading in VRAM...</span>
                </>
              ) : (
                <>
                  <Layers className="w-4 h-4" />
                  <span>Load / Switch Model</span>
                </>
              )}
            </button>

            {currentModel && (
              <button
                type="button"
                onClick={handleUnload}
                disabled={isLoading}
                className="py-3 px-4 rounded-xl bg-red-50 hover:bg-red-100 dark:bg-red-950/30 dark:hover:bg-red-900/40 border border-red-200 dark:border-red-900/50 text-red-600 dark:text-red-400 text-xs font-semibold transition-all flex items-center justify-center gap-1.5 min-h-[44px]"
                title="Completely unload active model"
              >
                <Power className="w-4 h-4" />
                <span>Unload</span>
              </button>
            )}
          </div>

        </form>

      </div>
    </div>
  );
}
