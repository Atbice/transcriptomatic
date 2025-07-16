import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ command, mode }) => {
  const config = {
    plugins: [react()],
    server: {
      port: 3000,
      hmr: {
        overlay: true,
      },
      proxy: {
        '/api': {
          target: 'http://backend:8000',
          changeOrigin: true,
        },
      },
    },
    build: {
      outDir: 'dist', // Output stays at /app/dist/
      assetsDir: 'assets',
    },
  };

  if (command === 'build') {
    const homeLabUrl = 'http://192.168.1.111:80';
    config.define = {
      'process.env.API_BASE_URL': JSON.stringify(`${homeLabUrl}/api`),
    };
  }

  return config;
});