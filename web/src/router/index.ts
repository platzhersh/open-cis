import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('@/pages/DashboardPage.vue'),
    },
    {
      path: '/patients',
      name: 'patients',
      component: () => import('@/pages/patients/PatientListPage.vue'),
    },
    {
      path: '/patients/:id',
      name: 'patient-detail',
      component: () => import('@/pages/patients/PatientDetailPage.vue'),
    },
  ],
})

export default router
