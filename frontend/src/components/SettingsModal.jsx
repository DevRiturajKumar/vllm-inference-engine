import React, { useState } from 'react';
import { 
  X, 
  Settings, 
  Radio, 
  Check, 
  AlertCircle, 
  RotateCcw, 
  Loader2,
  ExternalLink,
  Zap
} from 'lucide-react';
import { useSettings } from '../context/SettingsContext';
import { fetchHealth } from '../services/api';

export function SettingsModal({ isOpen, onClose, onConnectionChanged }) {
  const { settings, updateSettings, resetSettings } = useSettings();
  
  const [testUrl, setTestUrl] = useState(settings.baseUrl);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);

  if (!isOpen) return null;

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    const startTime = performance.now();

    try {
      const target = testUrl ? testUrl.trim().replace(/\/+$/, '') : '';
      const data = await fetchHealth(target);
      const latency = Math.round(performance.now() - startTime);
      setTestResult({
        success: true,
        latency,
        status: data.status,
        model: data.loaded_model,
        gpu: data.gpu_name || 'GPU Detected',
      });
      // Update persistent settings on success
      updateSettings({ baseUrl: target });
      if (onConnectionChanged) onConnectionChanged();
    } catch (err) {
      setTestResult({
        success: false,
        error: err.message || 'Unable to connect to vLLM server',
      });
    } finally {
      setTesting(false);
    }
  };

  const handleSave = (e) => {
    e.preventDefault();
    const target = testUrl ? testUrl.trim().replace(/\/+$/, '') : '';
    updateSettings({ baseUrl: target });
    if (onConnectionChanged) onConnectionChanged();
    onClose();
  };

  const handleReset = () => {
    resetSettings();
    setTestUrl('');
    setTestResult(null);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 animate-fade-in">
      {/* Backdrop */}
      <div 
        onClick={onClose}
        className="fixed inset-0 bg-black/60 backdrop-blur-sm" 
      />

      {/* Dialog */}
      <div className="relative w-full max-w-lg bg-white dark:bg-[#0f172a] rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl overflow-hidden z-10">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200/80 dark:border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-500">
              <Settings className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Connection Settings
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Configure vLLM FastAPI backend endpoint
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

        {/* Body */}
        <form onSubmit={handleSave} className="p-6 space-y-5 text-slate-800 dark:text-slate-200">
          
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
              API Base URL
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={testUrl}
                onChange={(e) => {
                  setTestUrl(e.target.value);
                  setTestResult(null);
                }}
                placeholder="Leave empty for Vite proxy, or enter https://<tunnel>.trycloudflare.com"
                className="flex-1 px-3.5 py-2.5 text-xs font-mono rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500/40"
              />
              <button
                type="button"
                onClick={handleTestConnection}
                disabled={testing}
                className="px-3.5 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-xs font-medium text-slate-700 dark:text-slate-200 transition-colors flex items-center gap-1.5 border border-slate-200 dark:border-slate-700 min-h-[44px]"
              >
                {testing ? <Loader2 className="w-4 h-4 animate-spin text-brand-500" /> : <Radio className="w-4 h-4 text-brand-500" />}
                <span>Test</span>
              </button>
            </div>
            <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-1.5">
              {testUrl ? (
                <>Connecting directly to: <code>{testUrl}</code></>
              ) : (
                <>Using default Vite proxy (configured in <code>vite.config.js</code> or <code>.env</code>)</>
              )}
            </p>
          </div>

          {/* Test Connection Results Card */}
          {testResult && (
            <div className={`p-3.5 rounded-2xl border text-xs ${
              testResult.success 
                ? 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-900/60 text-emerald-800 dark:text-emerald-300' 
                : 'bg-red-50 dark:bg-red-950/40 border-red-200 dark:border-red-900/60 text-red-700 dark:text-red-400'
            }`}>
              <div className="flex items-center gap-2 font-semibold mb-1">
                {testResult.success ? <Check className="w-4 h-4 text-emerald-500" /> : <AlertCircle className="w-4 h-4 text-red-500" />}
                <span>{testResult.success ? `Connected Successfully (${testResult.latency} ms)` : 'Connection Failed'}</span>
              </div>
              {testResult.success ? (
                <div className="space-y-0.5 text-[11px] opacity-90">
                  <div>Status: <span className="font-mono">{testResult.status}</span></div>
                  <div>GPU: <span className="font-mono">{testResult.gpu}</span></div>
                  {testResult.model && <div>Model: <span className="font-mono">{testResult.model}</span></div>}
                </div>
              ) : (
                <div className="text-[11px] opacity-90">{testResult.error}</div>
              )}
            </div>
          )}

          {/* Documentation / Info note */}
          <div className="p-3.5 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs text-slate-500 dark:text-slate-400 space-y-1">
            <div className="font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-brand-500" /> Completely Decoupled Frontend
            </div>
            <p className="text-[11px]">
              This UI is 100% portable. You can move this <code>frontend/</code> folder anywhere, host it on Cloudflare Pages or Vercel, and point it to any vLLM instance.
            </p>
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-between pt-2">
            <button
              type="button"
              onClick={handleReset}
              className="text-xs text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 flex items-center gap-1 py-2"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset Defaults</span>
            </button>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-xl text-xs font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 min-h-[44px]"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-5 py-2 rounded-xl bg-brand-500 hover:bg-brand-600 text-white text-xs font-semibold shadow-md shadow-brand-500/25 transition-all min-h-[44px]"
              >
                Save & Apply
              </button>
            </div>
          </div>

        </form>

      </div>
    </div>
  );
}
