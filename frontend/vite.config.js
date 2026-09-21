import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const rawTarget = env.VITE_BACKEND_URL || env.VITE_API_BASE_URL || 'http://127.0.0.1:8006';
  const backendTarget = rawTarget
    .trim()
    .replace(/\/+$/, '')
    .replace(/\/(docs|redoc)(#.*)?$/i, '')
    .replace(/\/+$/, '');

  return {
    plugins: [react()],
    server: {
      port: 3000,
      host: '127.0.0.1', // strictly localhost only
      allowedHosts: true,
      proxy: {
        '/v1': {
          target: backendTarget,
          changeOrigin: true,
          secure: false,
        },
        '/health': {
          target: backendTarget,
          changeOrigin: true,
          secure: false,
        },
        '/admin': {
          target: backendTarget,
          changeOrigin: true,
          secure: false,
        },
      },
    },
  };
});
