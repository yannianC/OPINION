import { createApp } from 'vue'
import { createRouter, createWebHistory, createWebHashHistory } from 'vue-router'
import { routes } from 'vue-router/auto-routes'
import App from './App.vue'

import type { UserModule } from './types'

import '~/styles/index.scss'
import 'uno.css'

// Element Plus 样式
import 'element-plus/theme-chalk/src/message.scss'
import 'element-plus/theme-chalk/src/message-box.scss'
import 'element-plus/theme-chalk/src/overlay.scss'

const app = createApp(App)

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes,
})

app.use(router)

// 自动安装 modules 文件夹下的插件
Object.values(import.meta.glob<{ install: UserModule }>('./modules/*.ts', { eager: true }))
  .forEach(i => i.install?.({ app, router }))

app.mount('#app')
