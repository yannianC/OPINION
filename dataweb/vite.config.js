import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  base: '/OpPloyData/',  // 设置基础路径以支持子目录部署
  server: {
    host: '0.0.0.0',  // 允许通过本地IP访问
    port: 3000,
    open: true,
    proxy: {
      '/api/opinion': {
        target: 'http://opinion.api.predictscan.dev:10001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/opinion/, '/api')
      }
    }
  }
})

