<script setup>
import { onMounted } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { useSession } from '@/composables/useSession'

const route = useRoute()
const { profile, ensureProfileLoaded } = useSession()

onMounted(() => {
  ensureProfileLoaded()
})
</script>

<template>
  <div class="app-shell">
    <header class="naver-nav shadow-sm">
      <div class="container naver-nav__inner">
        <div>
          <RouterLink class="naver-logo" to="/">Codex Platform</RouterLink>
          <p class="naver-subtitle mb-1">간결한 네이버 스타일 UI로 게시판·채팅·계정을 관리하세요.</p>
          <small class="text-muted">
            <span v-if="profile">로그인: {{ profile.user.username }}</span>
            <span v-else>로그인되지 않았습니다</span>
          </small>
        </div>
        <div class="nav-stack" aria-label="3단 네비게이션">
          <RouterLink to="/boards" class="nav-pill" :class="{ active: route.name === 'boards' }">게시판</RouterLink>
          <RouterLink to="/chat" class="nav-pill" :class="{ active: route.name === 'chat' }">채팅방</RouterLink>
          <RouterLink to="/accounts" class="nav-pill" :class="{ active: route.name === 'accounts' }">계정</RouterLink>
        </div>
      </div>
    </header>

    <main class="container py-4">
      <RouterView />
    </main>

    <footer class="text-center text-muted small py-4">
      <span class="me-2">Backend · Django REST</span>
      <span class="me-2">Frontend · Vue + Bootstrap</span>
      <span>Storage · AWS S3</span>
    </footer>
  </div>
</template>
