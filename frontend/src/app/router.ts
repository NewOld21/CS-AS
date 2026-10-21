import { createRouter, createWebHistory } from 'vue-router'
import LandingPage from './pages/LandingPage.vue'
export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: LandingPage, meta: { title: '지식의 궤도를, 나만의 속도로' } },
    {
      path: '/login',
      component: () => import('../domains/auth/AuthPage.vue'),
      meta: { title: '로그인' },
    },
    {
      path: '/signup',
      component: () => import('../domains/auth/AuthPage.vue'),
      meta: { title: '회원가입' },
    },
    {
      path: '/account',
      component: () => import('../domains/auth/AccountPage.vue'),
      meta: { title: '내 계정' },
    },
    {
      path: '/:pathMatch(.*)*',
      component: () => import('./pages/NotFoundPage.vue'),
      meta: { title: '페이지를 찾을 수 없어요' },
    },
  ],
  scrollBehavior(to) {
    return to.hash
      ? {
          el: to.hash,
          behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth',
        }
      : { top: 0 }
  },
})
router.afterEach((to) => {
  document.title = `${String(to.meta.title)} | CS/AS`
})
