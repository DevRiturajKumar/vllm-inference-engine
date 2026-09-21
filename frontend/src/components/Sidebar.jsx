import React, { useState } from 'react';
import { 
  Activity, 
  Cpu, 
  HardDrive, 
  RefreshCw, 
  Layers, 
  Sliders, 
  Flame, 
  Hash, 
  Brain, 
  RotateCcw, 
  Trash2, 
  Power,
  ChevronDown,
  ChevronUp,
  MessageSquare
} from 'lucide-react';
import { useSettings } from '../context/SettingsContext';
import { formatModelName } from '../utils/format';

export function Sidebar({ 
  healthData, 
  healthLoading, 
  onRefreshHealth, 
  onOpenModelManager, 
  onUnloadModel, 
  onClearChat,
  isMobileDrawerOpen,
  setIsMobileDrawerOpen
}) {
  const { settings, updateSettings } = useSettings();
  const [paramsExpanded, setParamsExpanded] = useState(true);
  const [promptExpanded, setPromptExpanded] = useState(true);

  // VRAM calculation & Granular Breakdown
  let vramAllocated = healthData?.vram_allocated_gb || 0;
  const vramTotal = healthData?.vram_total_gb || 16;
  
  let isEstimated = false;
  // If backend reported 0 GB but model is loaded and GPU is active:
  // vLLM pre-allocates ~85% of GPU memory for weights + KV cache in worker process
  if (vramAllocated === 0 && healthData?.status === 'OK' && vramTotal > 0) {
    vramAllocated = Math.round(vramTotal * 0.85 * 10) / 10;
    isEstimated = true;
  }

  let modelWeights = healthData?.model_weights_gb || 0;
  let kvCache = healthData?.kv_cache_paged_gb || 0;
  let vramFree = healthData?.vram_free_gb;

  if (healthData?.status === 'OK' && vramAllocated > 0) {
    if (modelWeights === 0) {
      // Fallback estimate: ~20% of GPU for 1.5B weights, rest is KV cache
      modelWeights = Math.min(Math.round(vramAllocated * 0.25 * 10) / 10, 3.1);
      kvCache = Math.max(Math.round((vramAllocated - modelWeights) * 10) / 10, 0);
    }
  }

  if (vramFree === undefined || vramFree === null) {
    vramFree = vramTotal > vramAllocated ? Math.round((vramTotal - vramAllocated) * 10) / 10 : 0;
  }

  const vramPercent = vramTotal > 0 ? Math.min(Math.round((vramAllocated / vramTotal) * 100), 100) : 0;
  const weightsPercent = vramTotal > 0 ? Math.min(Math.round((modelWeights / vramTotal) * 100), 100) : 0;
  const kvPercent = vramTotal > 0 ? Math.min(Math.round((kvCache / vramTotal) * 100), 100) : 0;

  const getVramColor = (pct) => {
    if (pct > 85) return 'bg-red-500';
    if (pct > 70) return 'bg-amber-500';
    return 'bg-brand-500';
  };

  const loadedModel = healthData?.loaded_model;

  const renderContent = () => (
    <div className="p-4 space-y-4 pb-28 text-slate-800 dark:text-slate-200">
      
      {/* 1. GPU / Health Monitor Card */}
      <div className="rounded-2xl bg-white dark:bg-slate-900/90 p-4 border border-slate-200/80 dark:border-slate-800 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <div className="p-1.5 rounded-lg bg-brand-500/10 text-brand-600 dark:text-brand-400">
              <Activity className="w-4 h-4" />
            </div>
            <span className="font-semibold text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400">
              GPU & VRAM Status
            </span>
          </div>

          <button
            onClick={onRefreshHealth}
            type="button"
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors min-h-[36px] min-w-[36px] flex items-center justify-center"
            title="Refresh GPU Metrics"
            aria-label="Refresh GPU Metrics"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${healthLoading ? 'animate-spin text-brand-500' : ''}`} />
          </button>
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center space-x-1.5 text-slate-600 dark:text-slate-300">
              <Cpu className="w-3.5 h-3.5 text-slate-400" />
              <span className="font-medium">{healthData?.gpu_name || (healthData?.gpu_available ? 'Active GPU' : 'No GPU Detected')}</span>
            </div>
            <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
              healthData?.status === 'OK' 
                ? 'bg-brand-500/10 text-brand-600 dark:text-brand-400 border border-brand-500/20' 
                : healthData?.status === 'READY_NO_MODEL'
                ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20'
                : 'bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20'
            }`}>
              {healthData?.status || 'OFFLINE'}
            </span>
          </div>

          {healthData?.gpu_available && (
            <div className="space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-500 dark:text-slate-400 flex items-center gap-1">
                  <HardDrive className="w-3 h-3" /> VRAM Allocation {isEstimated && <span className="text-[10px] text-brand-600 dark:text-brand-400 font-medium">(Reserved)</span>}
                </span>
                <span className="font-mono text-xs font-semibold text-slate-700 dark:text-slate-300">
                  {vramAllocated} GB / {vramTotal} GB ({vramPercent}%)
                </span>
              </div>

              {/* Segmented VRAM Bar */}
              <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2.5 overflow-hidden border border-slate-200/50 dark:border-slate-700/50 flex">
                {modelWeights > 0 && (
                  <div 
                    className="h-full bg-indigo-500 transition-all duration-500"
                    style={{ width: `${weightsPercent}%` }}
                    title={`Model Weights: ${modelWeights} GB (${weightsPercent}%)`}
                  />
                )}
                {kvCache > 0 && (
                  <div 
                    className="h-full bg-emerald-500 transition-all duration-500"
                    style={{ width: `${kvPercent}%` }}
                    title={`Paged KV Cache: ${kvCache} GB (${kvPercent}%)`}
                  />
                )}
                {modelWeights === 0 && kvCache === 0 && vramAllocated > 0 && (
                  <div 
                    className={`h-full transition-all duration-500 ${getVramColor(vramPercent)}`}
                    style={{ width: `${vramPercent}%` }}
                  />
                )}
              </div>

              {/* Detailed Breakdown Legend */}
              <div className="grid grid-cols-3 gap-1.5 pt-1 text-[11px]">
                <div className="p-1.5 rounded-xl bg-indigo-50/70 dark:bg-indigo-950/30 border border-indigo-200/50 dark:border-indigo-900/40">
                  <div className="flex items-center gap-1 text-indigo-700 dark:text-indigo-400 font-medium">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
                    <span>Weights</span>
                  </div>
                  <div className="font-mono font-semibold text-slate-800 dark:text-slate-200 mt-0.5">
                    {modelWeights} GB
                  </div>
                </div>

                <div className="p-1.5 rounded-xl bg-emerald-50/70 dark:bg-emerald-950/30 border border-emerald-200/50 dark:border-emerald-900/40">
                  <div className="flex items-center gap-1 text-emerald-700 dark:text-emerald-400 font-medium">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                    <span>KV Cache</span>
                  </div>
                  <div className="font-mono font-semibold text-slate-800 dark:text-slate-200 mt-0.5">
                    {kvCache} GB
                  </div>
                </div>

                <div className="p-1.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/50 dark:border-slate-700/40">
                  <div className="flex items-center gap-1 text-slate-600 dark:text-slate-400 font-medium">
                    <span className="w-1.5 h-1.5 rounded-full bg-slate-400 dark:bg-slate-500" />
                    <span>Free</span>
                  </div>
                  <div className="font-mono font-semibold text-slate-800 dark:text-slate-200 mt-0.5">
                    {vramFree} GB
                  </div>
                </div>
              </div>

            </div>
          )}
        </div>
      </div>

      {/* 2. Active Model Card */}
      <div className="rounded-2xl bg-white dark:bg-slate-900/90 p-4 border border-slate-200/80 dark:border-slate-800 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <div className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-600 dark:text-indigo-400">
              <Layers className="w-4 h-4" />
            </div>
            <span className="font-semibold text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Hosted Model
            </span>
          </div>
        </div>

        {loadedModel ? (
          <div className="space-y-3">
            <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/60 dark:border-slate-700/60">
              <p className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                {formatModelName(loadedModel)}
              </p>
              <p className="text-[10px] font-mono text-slate-400 dark:text-slate-500 truncate" title={loadedModel}>
                {loadedModel}
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={onOpenModelManager}
                type="button"
                className="flex-1 py-2 px-3 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-xs font-medium text-slate-700 dark:text-slate-200 transition-colors flex items-center justify-center gap-1.5 min-h-[40px]"
              >
                <Layers className="w-3.5 h-3.5 text-brand-500" />
                <span>Switch</span>
              </button>

              <button
                onClick={onUnloadModel}
                type="button"
                className="py-2 px-3 rounded-xl bg-red-50 hover:bg-red-100 dark:bg-red-950/30 dark:hover:bg-red-900/40 text-xs font-medium text-red-600 dark:text-red-400 transition-colors flex items-center justify-center gap-1.5 border border-red-200/60 dark:border-red-900/50 min-h-[40px]"
                title="Unload model from VRAM"
              >
                <Power className="w-3.5 h-3.5" />
                <span>Unload</span>
              </button>
            </div>
          </div>
        ) : (
          <div className="text-center py-3 space-y-2">
            <p className="text-xs text-slate-500 dark:text-slate-400">No model loaded in VRAM</p>
            <button
              onClick={onOpenModelManager}
              type="button"
              className="w-full py-2 px-3 rounded-xl bg-brand-500 hover:bg-brand-600 text-white text-xs font-medium shadow-md shadow-brand-500/20 transition-colors min-h-[40px] flex items-center justify-center gap-1.5"
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Load Model Now</span>
            </button>
          </div>
        )}
      </div>

      {/* 3. Inference Parameters Accordion */}
      <div className="rounded-2xl bg-white dark:bg-slate-900/90 border border-slate-200/80 dark:border-slate-800 shadow-sm overflow-hidden">
        <button
          onClick={() => setParamsExpanded(!paramsExpanded)}
          type="button"
          className="w-full flex items-center justify-between p-4 text-left select-none hover:bg-slate-50/50 dark:hover:bg-slate-800/40 transition-colors min-h-[48px]"
        >
          <div className="flex items-center space-x-2">
            <div className="p-1.5 rounded-lg bg-amber-500/10 text-amber-600 dark:text-amber-400">
              <Sliders className="w-4 h-4" />
            </div>
            <span className="font-semibold text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Sampling Parameters
            </span>
          </div>
          {paramsExpanded ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
        </button>

        {paramsExpanded && (
          <div className="px-4 pb-4 space-y-4 border-t border-slate-100 dark:border-slate-800 pt-3">
            {/* Thinking / Reasoning Toggle */}
            <div className="flex items-center justify-between p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20">
              <div className="flex items-center space-x-2">
                <Brain className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                <div>
                  <div className="text-xs font-semibold text-amber-900 dark:text-amber-200">
                    Chain of Thought (CoT)
                  </div>
                  <div className="text-[10px] text-amber-700/80 dark:text-amber-400/80">
                    Parse &lt;think&gt; reasoning tokens
                  </div>
                </div>
              </div>
              <input
                type="checkbox"
                checked={settings.enableThinking}
                onChange={(e) => updateSettings({ enableThinking: e.target.checked })}
                className="w-4 h-4 text-brand-600 rounded focus:ring-brand-500 accent-brand-500 cursor-pointer"
              />
            </div>

            {/* Temperature */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-slate-600 dark:text-slate-300 flex items-center gap-1">
                  <Flame className="w-3.5 h-3.5 text-amber-500" /> Temperature
                </span>
                <span className="font-mono font-semibold text-slate-700 dark:text-slate-300">
                  {settings.temperature}
                </span>
              </div>
              <input
                type="range"
                min="0.0"
                max="1.5"
                step="0.05"
                value={settings.temperature}
                onChange={(e) => updateSettings({ temperature: parseFloat(e.target.value) })}
                className="w-full accent-brand-500 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg cursor-pointer"
              />
            </div>

            {/* Top P */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-slate-600 dark:text-slate-300 flex items-center gap-1">
                  <Sliders className="w-3.5 h-3.5 text-indigo-500" /> Top P
                </span>
                <span className="font-mono font-semibold text-slate-700 dark:text-slate-300">
                  {settings.topP}
                </span>
              </div>
              <input
                type="range"
                min="0.1"
                max="1.0"
                step="0.05"
                value={settings.topP}
                onChange={(e) => updateSettings({ topP: parseFloat(e.target.value) })}
                className="w-full accent-brand-500 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg cursor-pointer"
              />
            </div>

            {/* Max Tokens */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-slate-600 dark:text-slate-300 flex items-center gap-1">
                  <Hash className="w-3.5 h-3.5 text-emerald-500" /> Max Tokens
                </span>
                <span className="font-mono font-semibold text-slate-700 dark:text-slate-300">
                  {settings.maxTokens}
                </span>
              </div>
              <input
                type="range"
                min="64"
                max="4096"
                step="64"
                value={settings.maxTokens}
                onChange={(e) => updateSettings({ maxTokens: parseInt(e.target.value) })}
                className="w-full accent-brand-500 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg cursor-pointer"
              />
            </div>
          </div>
        )}
      </div>

      {/* 4. System Prompt Accordion */}
      <div className="rounded-2xl bg-white dark:bg-slate-900/90 border border-slate-200/80 dark:border-slate-800 shadow-sm overflow-hidden">
        <button
          onClick={() => setPromptExpanded(!promptExpanded)}
          type="button"
          className="w-full flex items-center justify-between p-4 text-left select-none hover:bg-slate-50/50 dark:hover:bg-slate-800/40 transition-colors min-h-[48px]"
        >
          <div className="flex items-center space-x-2">
            <div className="p-1.5 rounded-lg bg-slate-500/10 text-slate-600 dark:text-slate-400">
              <MessageSquare className="w-4 h-4" />
            </div>
            <span className="font-semibold text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400">
              System Prompt
            </span>
          </div>
          {promptExpanded ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
        </button>

        {promptExpanded && (
          <div className="px-4 pb-4 space-y-2 border-t border-slate-100 dark:border-slate-800 pt-3">
            <div className="flex justify-end">
              <button
                onClick={() => updateSettings({ systemPrompt: 'You are a helpful, concise, and capable AI assistant.' })}
                type="button"
                className="text-[11px] text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 flex items-center gap-1"
                title="Reset system prompt to default"
              >
                <RotateCcw className="w-3 h-3" /> Reset
              </button>
            </div>
            <textarea
              rows={3}
              value={settings.systemPrompt}
              onChange={(e) => updateSettings({ systemPrompt: e.target.value })}
              placeholder="Enter system instructions..."
              className="w-full p-2.5 text-xs rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500/50 resize-none font-sans"
            />
          </div>
        )}
      </div>

      {/* 5. Clear Chat Action */}
      <div className="pt-2">
        <button
          onClick={onClearChat}
          type="button"
          className="w-full py-2.5 px-3 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800/80 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-medium transition-colors flex items-center justify-center gap-2 border border-slate-200/80 dark:border-slate-700/60 min-h-[44px]"
        >
          <Trash2 className="w-4 h-4 text-slate-500" />
          <span>Clear Chat History</span>
        </button>
      </div>

    </div>
  );

  return (
    <>
      {/* Desktop Sidebar (Fixed Left Column >= 1024px) */}
      <aside className="hidden lg:flex flex-col w-80 xl:w-84 flex-shrink-0 h-full border-r border-slate-200/80 dark:border-slate-800/80 bg-slate-50/50 dark:bg-[#0b0f19]/50 overflow-hidden">
        <div className="flex-1 overflow-y-auto overscroll-contain">
          {renderContent()}
        </div>
      </aside>

      {/* Mobile Drawer (Slide-in Modal < 1024px) */}
      {isMobileDrawerOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          {/* Backdrop blur */}
          <div 
            onClick={() => setIsMobileDrawerOpen(false)}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity" 
          />

          {/* Drawer content */}
          <div className="relative w-84 max-w-[85vw] h-full bg-slate-50 dark:bg-[#0b0f19] border-r border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col z-10 animate-slide-right overflow-hidden">
            <div className="p-3.5 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center safe-top flex-shrink-0 bg-white/70 dark:bg-slate-900/70 backdrop-blur-sm">
              <span className="font-bold text-sm text-slate-900 dark:text-white flex items-center gap-2">
                <Sliders className="w-4 h-4 text-brand-500" /> Controls & Health
              </span>
              <button
                onClick={() => setIsMobileDrawerOpen(false)}
                className="p-2 rounded-xl text-slate-500 hover:bg-slate-200 dark:hover:bg-slate-800 min-h-[44px] min-w-[44px] flex items-center justify-center"
                aria-label="Close Controls"
              >
                ✕
              </button>
            </div>
            <div className="flex-1 overflow-y-auto overscroll-contain safe-bottom">
              {renderContent()}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
