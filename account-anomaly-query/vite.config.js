import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  base: './',  // 使用相对路径，支持刷新时保持路由
  server: {
    port: 3001,
    host: '0.0.0.0'
  }
})

