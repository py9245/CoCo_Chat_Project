import { createRouter, createWebHistory } from 'vue-router'

const HomeView = () => import('@/views/HomeView.vue')
const BoardsView = () => import('@/views/BoardsView.vue')
const AccountsView = () => import('@/views/AccountsView.vue')
const ChatView = () => import('@/views/ChatView.vue')

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior() {
    return { top: 0 }
  },
  routes: [
    { path: '/', name: 'home', component: HomeView, meta: { title: '메인' } },
    { path: '/boards', name: 'boards', component: BoardsView, meta: { title: '게시판' } },
    { path: '/accounts', name: 'accounts', component: AccountsView, meta: { title: '계정' } },
    { path: '/chat', name: 'chat', component: ChatView, meta: { title: '채팅방' } },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.beforeEach((to, _from, next) => {
  document.title = `Codex · ${to.meta.title || '앱'}`
  next()
})

export default router
