import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/Login.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      component: () => import('@/layouts/DashboardLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('@/views/Dashboard.vue')
        },
        {
          path: 'programs',
          name: 'programs',
          component: () => import('@/views/Programs/ProgramList.vue')
        },
        {
          path: 'programs/:id',
          name: 'program-detail',
          component: () => import('@/views/Programs/ProgramDetail.vue')
        },
        {
          path: 'programs/:id/builder',
          name: 'program-builder',
          component: () => import('@/views/Programs/ProgramBuilder.vue')
        },
        {
          path: 'programs/new',
          name: 'program-new',
          component: () => import('@/views/Programs/ProgramBuilder.vue')
        },
        {
          path: 'campaigns',
          name: 'campaigns',
          component: () => import('@/views/Campaigns/CampaignList.vue')
        },
        {
          path: 'campaigns/:id',
          name: 'campaign-detail',
          component: () => import('@/views/Campaigns/CampaignDetail.vue')
        },
        {
          path: 'campaigns/:id/builder',
          name: 'campaign-builder',
          component: () => import('@/views/Campaigns/CampaignBuilder.vue')
        },
        {
          path: 'campaigns/new',
          name: 'campaign-new',
          component: () => import('@/views/Campaigns/CampaignBuilder.vue')
        },
        {
          path: 'segments',
          name: 'segments',
          component: () => import('@/views/Segments/SegmentList.vue')
        },
        {
          path: 'segments/:id',
          name: 'segment-detail',
          component: () => import('@/views/Segments/SegmentDetail.vue')
        },
        {
          path: 'segments/:id/builder',
          name: 'segment-builder',
          component: () => import('@/views/Segments/SegmentBuilder.vue')
        },
        {
          path: 'customers',
          name: 'customers',
          component: () => import('@/views/Customers/CustomerList.vue')
        },
        {
          path: 'customers/:id',
          name: 'customer-360',
          component: () => import('@/views/Customers/Customer360.vue')
        },
        {
          path: 'gamification',
          name: 'gamification',
          component: () => import('@/views/Gamification/GamificationDashboard.vue')
        },
        {
          path: 'customers/:id',
          name: 'customer-360',
          component: () => import('@/views/Customers/Customer360.vue')
        },
        {
          path: 'analytics',
          name: 'analytics',
          component: () => import('@/views/Analytics/AnalyticsDashboard.vue')
        },
        {
          path: 'journeys',
          name: 'journeys',
          component: () => import('@/views/Journeys/JourneyList.vue')
        },
        {
          path: 'journeys/:id/builder',
          name: 'journey-builder',
          component: () => import('@/views/Journeys/JourneyBuilder.vue')
        },
        {
          path: 'journeys/new/builder',
          name: 'journey-builder-new',
          component: () => import('@/views/Journeys/JourneyBuilder.vue')
        },
        {
          path: 'experiments',
          name: 'experiments',
          component: () => import('@/views/Experiments/ExperimentList.vue')
        },
        {
          path: 'experiments/:id',
          name: 'experiment-detail',
          component: () => import('@/views/Experiments/ExperimentDetail.vue')
        },
        {
          path: 'partners',
          name: 'partners',
          component: () => import('@/views/Partners/PartnerList.vue')
        },
        {
          path: 'partners/:id',
          name: 'partner-detail',
          component: () => import('@/views/Partners/PartnerDetail.vue')
        },
        {
          path: 'admin',
          name: 'admin',
          component: () => import('@/views/Admin/AdminDashboard.vue')
        }
      ]
    }
  ]
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  // If route requires auth and we have a token but no user, try to fetch user
  if (to.meta.requiresAuth && authStore.token && !authStore.user) {
    try {
      await authStore.fetchUser()
    } catch (error) {
      // Token is invalid, will be cleared by fetchUser
      console.error('Failed to fetch user:', error)
    }
  }
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})

export default router

