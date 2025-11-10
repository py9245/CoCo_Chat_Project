<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { useSession } from '@/composables/useSession'
import { logoutUser } from '@/services/api'

const route = useRoute()
const { profile, ensureProfileLoaded, clearSession } = useSession()
const isLoggingOut = ref(false)

onMounted(() => {
  ensureProfileLoaded()
})

const handleGlobalLogout = async () => {
  if (isLoggingOut.value) return
  isLoggingOut.value = true
  try {
    await logoutUser()
  } catch (error) {
    console.warn('전역 로그아웃에 실패했습니다.', error)
  } finally {
    clearSession()
    isLoggingOut.value = false
  }
}
</script>

<template>
  <div class="app-shell">
    <header class="naver-nav shadow-sm">
      <div class="container naver-nav__inner">
        <div>
          <RouterLink class="naver-logo" to="/">Codex Platform</RouterLink>
          <p class="naver-subtitle mb-1">간결한 네이버 스타일 UI로 게시판·채팅·계정을 관리하세요.</p>
          <div class="d-flex align-items-center gap-2 flex-wrap">
            <small class="text-muted mb-0">
              <span v-if="profile">로그인: {{ profile.user.username }}</span>
              <span v-else>로그인되지 않았습니다</span>
            </small>
            <button
              v-if="profile"
              class="btn btn-outline-light btn-sm nav-hover"
              type="button"
              :disabled="isLoggingOut"
              @click="handleGlobalLogout"
            >
              <span v-if="isLoggingOut">로그아웃 중...</span>
              <span v-else>로그아웃</span>
            </button>
            <RouterLink v-else class="btn btn-outline-light btn-sm nav-hover" to="/accounts">로그인</RouterLink>
          </div>
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
