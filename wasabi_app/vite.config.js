import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@src': path.resolve(import.meta.dirname, './src'), }
  },
  server: {
    host: '0.0.0.0', // Expose to local network/Docker containers
    port: 5173,      // Default Vite port
    strictPort: true,
    hmr: {
      clientPort: 80, // Force the browser to connect HMR to your NGINX port
    },
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
})
