import { createRouter, createWebHistory } from 'vue-router'

const HomeView = () => import('@/views/HomeView.vue')
const BoardsView = () => import('@/views/BoardsView.vue')
const AccountsView = () => import('@/views/AccountsView.vue')
const ChatView = () => import('@/views/ChatView.vue')
const ErdDocView = () => import('@/views/docs/ErdDocView.vue')
const ArchitectureDocView = () => import('@/views/docs/ArchitectureDocView.vue')
const RoadmapDocView = () => import('@/views/docs/RoadmapDocView.vue')

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior() {
    return { top: 0 }
  },
  routes: [
    { path: '/', name: 'home', component: HomeView, meta: { title: '메인' } },
    { path: '/boards', name: 'boards', component: BoardsView, meta: { title: '게시판' } },
    { path: '/accounts', name: 'accounts', component: AccountsView, meta: { title: '계정' } },
    { path: '/chat', name: 'chat', component: ChatView, meta: { title: '채팅방' } },
    { path: '/docs/erd', name: 'docs-erd', component: ErdDocView, meta: { title: 'ERD 다이어그램' } },
    {
      path: '/docs/architecture',
      name: 'docs-architecture',
      component: ArchitectureDocView,
      meta: { title: '아키텍처 흐름' },
    },
    { path: '/docs/roadmap', name: 'docs-roadmap', component: RoadmapDocView, meta: { title: '프로젝트 발전 과정' } },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.beforeEach((to, _from, next) => {
  document.title = `CoCo-Chat · ${to.meta.title || '앱'}`
  next()
})

export default router
