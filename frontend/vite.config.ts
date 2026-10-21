import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': {
        target: process.env.CSAS_API_TARGET ?? 'http://localhost:8080',
        changeOrigin: false,
      },
    },
  },
  test: { environment: 'jsdom', include: ['tests/unit/**/*.test.ts'], clearMocks: true },
})
