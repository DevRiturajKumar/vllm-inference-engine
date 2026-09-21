import React from 'react';
import { 
  Zap, 
  Layers, 
  Settings, 
  ExternalLink, 
  Menu, 
  X, 
  Activity,
  Cpu
} from 'lucide-react';
import { ThemeToggle } from './ThemeToggle';
import { useSettings } from '../context/SettingsContext';
import { formatModelName } from '../utils/format';

export function Header({ 
  healthData, 
  healthLoading, 
  onOpenModelManager, 
  onOpenSettings, 
  isMobileDrawerOpen, 
  setIsMobileDrawerOpen 
}) {
  const { settings } = useSettings();

  // Status computation
  const isHealthy = healthData?.status === 'OK';
  const isReadyNoModel = healthData?.status === 'READY_NO_MODEL';
  const isError = !healthLoading && !healthData;

  const loadedModel = healthData?.loaded_model;

  return (
    <header className="sticky top-0 z-30 w-full backdrop-blur-md bg-white/85 dark:bg-[#0b0f19]/85 border-b border-slate-200/80 dark:border-slate-800/80 safe-top transition-colors">
      <div className="max-w-7xl mx-auto px-3 sm:px-6 h-16 flex items-center justify-between gap-2">
        {/* Left: Brand Logo & Title */}
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setIsMobileDrawerOpen(!isMobileDrawerOpen)}
            type="button"
            className="lg:hidden p-2 rounded-xl text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 focus:outline-none min-h-[44px] min-w-[44px] flex items-center justify-center"
            aria-label={isMobileDrawerOpen ? 'Close Menu' : 'Open Menu'}
          >
            {isMobileDrawerOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>

          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 to-emerald-400 flex items-center justify-center text-white shadow-lg shadow-brand-500/25">
              <Zap className="w-5 h-5 fill-current" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-base sm:text-lg tracking-tight text-slate-900 dark:text-white">
                  vLLM Studio
                </span>
                <span className="hidden sm:inline-flex px-1.5 py-0.5 text-[10px] font-semibold tracking-wider rounded-md bg-brand-500/10 text-brand-600 dark:text-brand-400 border border-brand-500/20 uppercase">
                  v1.0
                </span>
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 hidden sm:block">
                High-Throughput Inference Engine
              </p>
            </div>
          </div>
        </div>

        {/* Center: Live Status Badge */}
        <div className="hidden md:flex items-center space-x-2 bg-slate-100 dark:bg-slate-800/60 py-1.5 px-3 rounded-full border border-slate-200/60 dark:border-slate-700/60 text-xs">
          <div className="flex items-center space-x-1.5">
            <span className="relative flex h-2 w-2">
              {isHealthy && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-400 opacity-75"></span>
              )}
              <span className={`relative inline-flex rounded-full h-2 w-2 ${
                isHealthy ? 'bg-brand-500' : isReadyNoModel ? 'bg-amber-400' : 'bg-red-500'
              }`}></span>
            </span>
            <span className="font-medium text-slate-700 dark:text-slate-300">
              {healthLoading ? 'Connecting...' : isHealthy ? 'Online' : isReadyNoModel ? 'Standby (No Model)' : 'Disconnected'}
            </span>
          </div>

          {healthData?.gpu_available && (
            <>
              <span className="text-slate-300 dark:text-slate-700">•</span>
              <div className="flex items-center space-x-1 text-slate-500 dark:text-slate-400">
                <Cpu className="w-3.5 h-3.5 text-slate-400" />
                <span>{healthData.gpu_name || 'GPU'}</span>
              </div>
            </>
          )}

          {loadedModel && (
            <>
              <span className="text-slate-300 dark:text-slate-700">•</span>
              <span className="font-semibold text-xs text-brand-600 dark:text-brand-400 truncate max-w-[170px]" title={loadedModel}>
                {formatModelName(loadedModel)}
              </span>
            </>
          )}
        </div>

        {/* Right: Actions & Theme Toggle */}
        <div className="flex items-center space-x-1.5 sm:space-x-2">
          <button
            onClick={onOpenModelManager}
            type="button"
            className="flex items-center space-x-1.5 px-2.5 sm:px-3 py-2 rounded-xl text-xs font-medium text-slate-700 dark:text-slate-200 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800/80 dark:hover:bg-slate-800 border border-slate-200/80 dark:border-slate-700/60 transition-colors min-h-[44px]"
            title="Manage and switch models"
          >
            <Layers className="w-4 h-4 text-brand-500" />
            <span className="hidden sm:inline">Model</span>
          </button>

          <button
            onClick={onOpenSettings}
            type="button"
            className="p-2 rounded-xl text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200/80 dark:border-slate-700/60 transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center"
            title="Connection Settings"
            aria-label="Connection Settings"
          >
            <Settings className="w-4 h-4" />
          </button>

          {/* External Swagger API Docs */}
          <a
            href={`${settings.baseUrl}/docs`}
            target="_blank"
            rel="noopener noreferrer"
            className="hidden sm:flex p-2 rounded-xl text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200/80 dark:border-slate-700/60 transition-colors min-h-[44px] min-w-[44px] items-center justify-center"
            title="View API Docs"
            aria-label="View API Docs"
          >
            <ExternalLink className="w-4 h-4" />
          </a>

          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
