import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/pages/auth/LoginPage.vue'),
      meta: { public: true },
    },
    {
      path: '/auth/callback',
      name: 'auth-callback',
      component: () => import('@/pages/auth/AuthCallbackPage.vue'),
      meta: { public: true },
    },
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
    {
      path: '/encounters',
      name: 'encounters',
      component: () => import('@/pages/encounters/EncounterListPage.vue'),
    },
    {
      path: '/encounters/:id',
      name: 'encounter-detail',
      component: () => import('@/pages/encounters/EncounterDetailPage.vue'),
    },
    {
      path: '/system',
      name: 'system',
      component: () => import('@/pages/SystemInfoPage.vue'),
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  // Allow public routes
  if (to.meta.public) return true

  // Redirect to login if not authenticated
  if (!auth.isAuthenticated) return '/login'

  // Fetch user profile if token exists but user not loaded
  if (!auth.user) {
    const success = await auth.fetchMe()
    if (!success) return '/login'
  }

  return true
})

export default router
