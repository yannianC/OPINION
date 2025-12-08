import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  base: '/OPPLOY/',  // 设置基础路径以支持子目录部署
  server: {
    port: 3000,
    host: '0.0.0.0'
  }
})

