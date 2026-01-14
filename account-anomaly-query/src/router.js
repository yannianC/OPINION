import { createRouter, createWebHashHistory } from 'vue-router'
import TaskAnomaly from './TaskAnomaly.vue'
import AccountAnomaly from './AccountAnomaly.vue'
import EventAnomaly from './EventAnomaly.vue'
import PositionDetail from './PositionDetail.vue'
import OpenOrderDetail from './OpenOrderDetail.vue'
import BrowserTaskInfo from './BrowserTaskInfo.vue'
import EventTaskInfo from './EventTaskInfo.vue'

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
  },
  {
    path: '/position-detail',
    name: 'PositionDetail',
    component: PositionDetail
  },
  {
    path: '/open-order-detail',
    name: 'OpenOrderDetail',
    component: OpenOrderDetail
  },
  {
    path: '/browser-task-info',
    name: 'BrowserTaskInfo',
    component: BrowserTaskInfo
  },
  {
    path: '/event-task-info',
    name: 'EventTaskInfo',
    component: EventTaskInfo
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router

