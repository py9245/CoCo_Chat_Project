<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { useSession } from '@/composables/useSession'
import { logoutUser } from '@/services/api'
import AuthorSidebar from '@/components/AuthorSidebar.vue'

const route = useRoute()
const { profile, ensureProfileLoaded, clearSession } = useSession()
const isLoggingOut = ref(false)
const isMobileViewport = ref(false)
const isNavOpen = ref(true)

const NAV_MOBILE_QUERY = '(max-width: 991.98px)'
let viewportQuery = null
let viewportListener = null

const syncViewportState = (matches) => {
  isMobileViewport.value = matches
  if (!matches) {
    isNavOpen.value = true
    return
  }
  isNavOpen.value = false
}

onMounted(() => {
  ensureProfileLoaded()
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
    isMobileViewport.value = false
    isNavOpen.value = true
    return
  }

  viewportQuery = window.matchMedia(NAV_MOBILE_QUERY)

  syncViewportState(viewportQuery.matches)

  viewportListener = (event) => {
    syncViewportState(event.matches)
  }

  viewportQuery.addEventListener('change', viewportListener)
})

onBeforeUnmount(() => {
  if (viewportQuery && viewportListener) {
    viewportQuery.removeEventListener('change', viewportListener)
  }
  viewportQuery = null
  viewportListener = null
})

const shouldShowToggle = computed(() => isMobileViewport.value)
const navVisible = computed(() => (isMobileViewport.value ? isNavOpen.value : true))

const toggleNav = () => {
  if (!isMobileViewport.value) return
  isNavOpen.value = !isNavOpen.value
}

const closeNav = () => {
  if (!isMobileViewport.value) return
  isNavOpen.value = false
}

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
    closeNav()
  }
}
</script>

<template>
  <div class="app-shell">
    <header class="naver-nav shadow-sm">
      <nav class="navbar navbar-expand-lg navbar-light bg-white">
        <div class="container">
          <RouterLink class="navbar-brand naver-logo" to="/">CoCo-Chat</RouterLink>
          <button
            v-if="shouldShowToggle"
            class="navbar-toggler"
            type="button"
            :aria-expanded="navVisible ? 'true' : 'false'"
            aria-controls="primaryNav"
            aria-label="네비게이션 토글"
            @click="toggleNav"
          >
            <span class="navbar-toggler-icon"></span>
          </button>
          <div
            id="primaryNav"
            :class="[
              'navbar-collapse',
              'app-navbar-collapse',
              {
                'app-navbar-collapse--open': navVisible,
              },
            ]"
          >
            <div class="navbar-text me-lg-4">
              <p class="naver-subtitle mb-1">랜덤 채팅, 게시판, 계정을 한 번에 관리하세요.</p>
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
                <RouterLink v-else class="btn btn-outline-light btn-sm nav-hover" to="/accounts" @click="closeNav">
                  로그인
                </RouterLink>
              </div>
            </div>
            <ul class="navbar-nav ms-auto mb-2 mb-lg-0 nav-stack">
              <li class="nav-item">
                <RouterLink :class="['nav-link', { active: route.name === 'boards' }]" to="/boards" @click="closeNav">
                  게시판
                </RouterLink>
              </li>
              <li class="nav-item">
                <RouterLink :class="['nav-link', { active: route.name === 'chat' }]" to="/chat" @click="closeNav">
                  채팅방
                </RouterLink>
              </li>
              <li class="nav-item">
                <RouterLink :class="['nav-link', { active: route.name === 'accounts' }]" to="/accounts" @click="closeNav">
                  계정
                </RouterLink>
              </li>
            </ul>
          </div>
        </div>
      </nav>
    </header>

    <main class="container py-4">
      <RouterView />
    </main>

    <footer class="text-center text-muted small py-4">
      <span class="me-2">Backend · Django REST</span>
      <span class="me-2">Frontend · Vue + Bootstrap</span>
      <span>Storage · AWS S3</span>
    </footer>
    <AuthorSidebar />
  </div>
</template>
