import React, { createContext, useContext, useState, useEffect } from 'react';

const SettingsContext = createContext();

const getInitialBaseUrl = () => {
  if (typeof import.meta !== 'undefined' && import.meta.env) {
    const raw = import.meta.env.VITE_BACKEND_URL || import.meta.env.VITE_API_BASE_URL;
    if (raw) {
      return raw
        .trim()
        .replace(/\/+$/, '')
        .replace(/\/(docs|redoc)(#.*)?$/i, '')
        .replace(/\/+$/, '');
    }
  }
  // Default to empty string so requests automatically route via relative path
  // through the Vite proxy or same-origin reverse proxy configured in vite.config.js
  return '';
};

const DEFAULT_SETTINGS = {
  baseUrl: getInitialBaseUrl(),
  selectedModel: '',
  systemPrompt: 'You are a helpful, concise, and capable AI assistant.',
  temperature: 0.7,
  topP: 0.9,
  topK: 50,
  maxTokens: 1024,
  repetitionPenalty: 1.05,
  enableThinking: false,
  syncedWithBackend: false,
  stream: true,
  autoScroll: true,
};

export function SettingsProvider({ children }) {
  const [settings, setSettings] = useState(() => {
    const envUrl = getInitialBaseUrl();
    try {
      const saved = localStorage.getItem('vllm_engine_settings');
      if (saved) {
        const parsed = JSON.parse(saved);
        // Force cleanup of any legacy domain cached in browser localStorage
        if (parsed.baseUrl && (parsed.baseUrl.includes('.me') || parsed.baseUrl.includes('cf.') || parsed.baseUrl.includes('159.'))) {
          parsed.baseUrl = envUrl;
        }
        // If an explicit backend URL is configured in frontend/.env, prioritize it
        if (envUrl) {
          parsed.baseUrl = envUrl;
        }
        // Clean any /docs or /redoc from stored URL
        if (parsed.baseUrl) {
          parsed.baseUrl = parsed.baseUrl.trim().replace(/\/+$/, '').replace(/\/(docs|redoc)(#.*)?$/i, '').replace(/\/+$/, '');
        }
        return { ...DEFAULT_SETTINGS, ...parsed };
      }
    } catch (e) {}
    return { ...DEFAULT_SETTINGS, baseUrl: envUrl };
  });

  useEffect(() => {
    try {
      localStorage.setItem('vllm_engine_settings', JSON.stringify(settings));
    } catch (e) {}
  }, [settings]);

  const updateSettings = (updates) => {
    setSettings(prev => ({ ...prev, ...updates }));
  };

  const resetSettings = () => {
    setSettings(DEFAULT_SETTINGS);
  };

  return (
    <SettingsContext.Provider value={{ settings, updateSettings, resetSettings }}>
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings() {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
}
