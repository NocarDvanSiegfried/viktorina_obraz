import path from "node:path"
import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"

const apiProxyTarget =
  process.env.VITE_DEV_API_TARGET ?? "http://127.0.0.1:8000"

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/quiz": {
        target: apiProxyTarget,
        changeOrigin: true,
      },
      "/student/start": {
        target: apiProxyTarget,
        changeOrigin: true,
      },
      "/student/questions": {
        target: apiProxyTarget,
        changeOrigin: true,
      },
      "/student/answer": {
        target: apiProxyTarget,
        changeOrigin: true,
      },
      "/student/finish": {
        target: apiProxyTarget,
        changeOrigin: true,
      },
      "/health": {
        target: apiProxyTarget,
        changeOrigin: true,
      },
    },
  },
})
