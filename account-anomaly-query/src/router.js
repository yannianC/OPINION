import { createRouter, createWebHistory } from 'vue-router'
import TaskAnomaly from './TaskAnomaly.vue'
import AccountAnomaly from './AccountAnomaly.vue'
import EventAnomaly from './EventAnomaly.vue'

const routes = [
  {
    path: '/',
    redirect: '/task-anomaly'
  },
  {
    path: '/task-anomaly',
    name: 'TaskAnomaly',
    component: TaskAnomaly
  },
  {
    path: '/account-anomaly',
    name: 'AccountAnomaly',
    component: AccountAnomaly
  },
  {
    path: '/event-anomaly',
    name: 'EventAnomaly',
    component: EventAnomaly
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

