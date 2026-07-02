import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

// Single-domain deployment: nginx serves the SPA and proxies /api etc. to the
// backend. For `npm run dev`, proxy the same paths to a backend on :8000.
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
      '/django-admin': { target: 'http://localhost:8000', changeOrigin: true },
      '/media': { target: 'http://localhost:8000', changeOrigin: true },
      '/static': { target: 'http://localhost:8000', changeOrigin: true }
    }
  },
  build: {
    chunkSizeWarningLimit: 1200
  }
});
