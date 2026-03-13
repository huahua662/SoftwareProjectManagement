import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
  { path: '/project/:id', name: 'ProjectDetail', component: () => import('../views/ProjectDetail.vue') },
  { path: '/project/:id/import', name: 'ChatImport', component: () => import('../views/ChatImport.vue') },
  { path: '/project/:id/requirement', name: 'RequirementDoc', component: () => import('../views/RequirementDoc.vue') },
  { path: '/project/:id/tasks', name: 'TaskBoard', component: () => import('../views/TaskBoard.vue') },
  { path: '/settings', name: 'Settings', component: () => import('../views/Settings.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
