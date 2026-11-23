import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const gatewayTarget = process.env.VITE_GATEWAY_URL || 'http://localhost:8080';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/auth': { target: gatewayTarget, changeOrigin: true },
      '/catalog': { target: gatewayTarget, changeOrigin: true },
      '/cart': { target: gatewayTarget, changeOrigin: true },
    },
  },
});