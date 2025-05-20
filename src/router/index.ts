import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import ReaderView from '../views/ReaderView.vue'
import KnowledgeGraphView from '../views/KnowledgeGraphView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/reader',
      name: 'reader',
      component: ReaderView
    },
    {
      path: '/knowledge-graph',
      name: 'knowledge-graph',
      component: KnowledgeGraphView
    },
    {
      path: '/knowledge-base',
      name: 'knowledge-base',
      component: () => import('../views/KnowledgeBaseView.vue')
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('../views/SettingsView.vue')
    }
  ]
})

export default router
