import type { App } from 'vue'
import type { Router } from 'vue-router'

interface AppContext {
  app: App<Element>
  router: Router
}

export type UserModule = (ctx: AppContext) => void
