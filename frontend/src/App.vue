<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import {
  fetchHealth,
  fetchMessages,
  fetchProfile,
  loginUser,
  logoutUser,
  registerUser,
  loadAuthToken,
  saveAuthToken,
  clearAuthToken,
  fetchChatMessages,
  postChatMessage,
} from '@/services/api'

const isLoading = ref(true)
const isRefreshing = ref(false)
const health = ref({
  ok: null,
  text: 'API 상태 확인 중...',
})
const messages = ref([])
const errorMessage = ref('')
const lastUpdated = ref(null)

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
})
const loginForm = reactive({
  username: '',
  password: '',
})
const authToken = ref(loadAuthToken())
const currentUser = ref(null)
const authMessage = ref('')
const authError = ref('')
const isRegistering = ref(false)
const isLoggingIn = ref(false)
const isLoggingOut = ref(false)
const chatMessages = ref([])
const chatForm = reactive({
  content: '',
  isAnonymous: true,
})
const isChatLoading = ref(true)
const isChatSending = ref(false)
const chatError = ref('')
const CHAT_HISTORY_LIMIT = 80
const CHAT_POLL_INTERVAL = 5000
let chatPollTimer = null

const canSendChat = computed(() => {
  if (!currentUser.value) return false
  return Boolean(chatForm.content.trim())
})

const timestamp = (date) =>
  new Intl.DateTimeFormat('ko-KR', {
    dateStyle: 'long',
    timeStyle: 'short',
  }).format(date)

const formatDate = (value) => {
  if (!value) return ''
  const date = typeof value === 'string' ? new Date(value) : value
  if (Number.isNaN(date.getTime())) return ''
  return timestamp(date)
}

const resetMessages = () => {
  authMessage.value = ''
  authError.value = ''
}

const extractErrorMessage = (error, fallback) => {
  if (error?.payload?.detail) return error.payload.detail
  if (error?.payload && typeof error.payload === 'object') {
    const merged = Object.values(error.payload)
      .flat()
      .filter((item) => typeof item === 'string')
    if (merged.length) return merged.join(' ')
  }
  return fallback
}

async function loadHealth() {
  try {
    const payload = await fetchHealth()
    health.value = {
      ok: Boolean(payload?.ok),
      text: payload?.ok ? 'API 정상 동작 중' : 'API 응답 이상',
    }
  } catch {
    health.value = {
      ok: false,
      text: 'API 응답 없음',
    }
  }
}

async function loadMessages() {
  try {
    const payload = await fetchMessages()
    messages.value = Array.isArray(payload?.messages) ? payload.messages : []
    errorMessage.value = ''
  } catch (error) {
    console.error(error)
    messages.value = []
    errorMessage.value = '메시지를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.'
  } finally {
    isLoading.value = false
    lastUpdated.value = new Date()
  }
}

async function refreshData() {
  if (isRefreshing.value) return
  isRefreshing.value = true
  try {
    await Promise.all([loadHealth(), loadMessages()])
  } finally {
    isRefreshing.value = false
  }
}

async function bootstrapAuth() {
  if (!authToken.value) return
  try {
    const payload = await fetchProfile()
    currentUser.value = payload?.user ?? null
  } catch (error) {
    console.warn('토큰 확인 실패', error)
    clearAuthToken()
    authToken.value = null
  }
}

function applySession(token, user) {
  saveAuthToken(token)
  authToken.value = token
  currentUser.value = user
}

async function loadChatMessages({ silent = false } = {}) {
  if (!silent) {
    isChatLoading.value = true
  }
  try {
    const payload = await fetchChatMessages({ limit: CHAT_HISTORY_LIMIT })
    chatMessages.value = Array.isArray(payload?.messages) ? payload.messages : []
    if (!silent) {
      chatError.value = ''
    }
  } catch (error) {
    console.error('채팅 로드 실패', error)
    chatError.value = '채팅 메시지를 불러오지 못했습니다.'
  } finally {
    if (!silent) {
      isChatLoading.value = false
    }
  }
}

function stopChatPolling() {
  if (chatPollTimer) {
    clearInterval(chatPollTimer)
    chatPollTimer = null
  }
}

function startChatPolling() {
  if (typeof window === 'undefined') return
  stopChatPolling()
  chatPollTimer = window.setInterval(() => {
    loadChatMessages({ silent: true })
  }, CHAT_POLL_INTERVAL)
}

async function handleChatSubmit() {
  if (!currentUser.value) {
    chatError.value = '로그인 후 이용해 주세요.'
    return
  }
  const content = chatForm.content.trim()
  if (!content) {
    chatError.value = '메시지를 입력해 주세요.'
    return
  }
  isChatSending.value = true
  try {
    const payload = await postChatMessage({
      content,
      is_anonymous: chatForm.isAnonymous,
    })
    chatMessages.value = [...chatMessages.value, payload].slice(-CHAT_HISTORY_LIMIT)
    chatForm.content = ''
    chatError.value = ''
  } catch (error) {
    chatError.value = extractErrorMessage(error, '메시지를 전송하지 못했습니다.')
  } finally {
    isChatSending.value = false
  }
}

async function handleRegister() {
  resetMessages()
  isRegistering.value = true
  try {
    const payload = await registerUser({
      username: registerForm.username.trim(),
      email: registerForm.email.trim(),
      password: registerForm.password,
    })
    applySession(payload.token, payload.user)
    authMessage.value = '회원가입이 완료되었습니다.'
    registerForm.username = ''
    registerForm.email = ''
    registerForm.password = ''
  } catch (error) {
    authError.value = extractErrorMessage(error, '회원가입에 실패했습니다.')
  } finally {
    isRegistering.value = false
  }
}

async function handleLogin() {
  resetMessages()
  isLoggingIn.value = true
  try {
    const payload = await loginUser({
      username: loginForm.username.trim(),
      password: loginForm.password,
    })
    applySession(payload.token, payload.user)
    authMessage.value = '로그인이 완료되었습니다.'
    loginForm.username = ''
    loginForm.password = ''
  } catch (error) {
    authError.value = extractErrorMessage(error, '로그인에 실패했습니다.')
  } finally {
    isLoggingIn.value = false
  }
}

async function handleLogout() {
  resetMessages()
  isLoggingOut.value = true
  try {
    await logoutUser()
  } catch (error) {
    console.warn('로그아웃 요청 실패', error)
  } finally {
    clearAuthToken()
    authToken.value = null
    currentUser.value = null
    authMessage.value = '로그아웃되었습니다.'
    isLoggingOut.value = false
  }
}

onMounted(async () => {
  await Promise.all([bootstrapAuth(), refreshData(), loadChatMessages()])
  startChatPolling()
})

onUnmounted(() => {
  stopChatPolling()
})
</script>

<template>
  <div class="page">
    <header class="hero">
      <div class="status">
        <span class="status-dot" :class="{ ok: health.ok === true, fail: health.ok === false }"></span>
        <span class="status-text">{{ health.text }}</span>
      </div>
      <h1>Docker · Django · Postgres · Vue</h1>
      <p class="subtitle">
        Vue SPA가 Django REST API(`/api/messages`)에서 데이터를 수집하고 바로 렌더링합니다.
      </p>

      <div class="toolbar">
        <button class="refresh" :disabled="isRefreshing" @click="refreshData">
          <span v-if="isRefreshing">새로 고치는 중...</span>
          <span v-else>목록 새로 고침</span>
        </button>
        <a class="toolbar-link" href="/chat.html">전체 채팅방 열기</a>
        <span v-if="lastUpdated" class="timestamp">마지막 갱신: {{ formatDate(lastUpdated) }}</span>
      </div>
    </header>

    <main>
      <section class="panel auth-panel">
        <h2>간단 회원 서비스</h2>
        <p class="panel-note">가입/로그인은 Django API(`/api/auth/*`)와 연동되어 토큰으로 인증됩니다.</p>

        <div v-if="currentUser" class="authed-box">
          <div>
            <p class="authed-title"><strong>{{ currentUser.username }}</strong> 님이 로그인 중입니다.</p>
            <p class="authed-subtitle">{{ currentUser.email || '이메일 정보 없음' }}</p>
          </div>
          <button class="logout-btn" :disabled="isLoggingOut" @click="handleLogout">
            <span v-if="isLoggingOut">로그아웃 중...</span>
            <span v-else>로그아웃</span>
          </button>
        </div>

        <div v-else class="auth-grid">
          <form class="auth-form" autocomplete="off" @submit.prevent="handleRegister">
            <h3>회원가입</h3>
            <label class="input-group">
              <span>아이디</span>
              <input
                v-model="registerForm.username"
                name="register-username"
                placeholder="예) ssafy_user"
                minlength="3"
                required
                autocomplete="username"
              />
            </label>
            <label class="input-group">
              <span>이메일</span>
              <input
                v-model="registerForm.email"
                type="email"
                name="register-email"
                placeholder="you@example.com"
                required
                autocomplete="email"
              />
            </label>
            <label class="input-group">
              <span>비밀번호</span>
              <input
                v-model="registerForm.password"
                type="password"
                name="register-password"
                placeholder="8자 이상"
                minlength="8"
                required
                autocomplete="new-password"
              />
            </label>
            <button class="primary-btn" :disabled="isRegistering" type="submit">
              <span v-if="isRegistering">가입 처리 중...</span>
              <span v-else>회원가입</span>
            </button>
          </form>

          <form class="auth-form" autocomplete="off" @submit.prevent="handleLogin">
            <h3>로그인</h3>
            <label class="input-group">
              <span>아이디</span>
              <input
                v-model="loginForm.username"
                name="login-username"
                placeholder="아이디를 입력하세요"
                required
                autocomplete="username"
              />
            </label>
            <label class="input-group">
              <span>비밀번호</span>
              <input
                v-model="loginForm.password"
                type="password"
                name="login-password"
                placeholder="비밀번호를 입력하세요"
                required
                autocomplete="current-password"
              />
            </label>
            <button class="primary-btn" :disabled="isLoggingIn" type="submit">
              <span v-if="isLoggingIn">로그인 중...</span>
              <span v-else>로그인</span>
            </button>
          </form>
        </div>

        <p v-if="authMessage" class="auth-message success">{{ authMessage }}</p>
        <p v-if="authError" class="auth-message error">{{ authError }}</p>
      </section>

      <section class="panel chat-panel">
        <header>
          <h2>실시간 자유 채팅방</h2>
          <p class="panel-note">로그인 후 익명 또는 아이디를 공개해 자유롭게 이야기해 보세요.</p>
        </header>

        <div v-if="isChatLoading" class="chat-empty">채팅 메시지를 불러오는 중...</div>
        <div v-else-if="!chatMessages.length" class="chat-empty">아직 대화가 없습니다. 첫 메시지를 남겨보세요!</div>
        <div v-else class="chat-messages">
          <article v-for="chat in chatMessages" :key="chat.id" class="chat-message">
            <div class="chat-meta">
              <span class="chat-display-name" :class="{ anonymous: chat.is_anonymous }">{{ chat.display_name }}</span>
              <time>{{ formatDate(chat.created_at) }}</time>
            </div>
            <p>{{ chat.content }}</p>
          </article>
        </div>

        <p v-if="chatError" class="chat-error">{{ chatError }}</p>

        <form v-if="currentUser" class="chat-form" autocomplete="off" @submit.prevent="handleChatSubmit">
          <label class="chat-toggle">
            <input v-model="chatForm.isAnonymous" type="checkbox" />
            <span>{{ chatForm.isAnonymous ? '익명으로 보내기' : '아이디 공개' }}</span>
          </label>
          <textarea
            v-model="chatForm.content"
            name="chat-content"
            placeholder="지금 떠오르는 생각을 적어보세요 (최대 500자)"
            maxlength="500"
          ></textarea>
          <button class="primary-btn" :disabled="isChatSending || !canSendChat" type="submit">
            <span v-if="isChatSending">전송 중...</span>
            <span v-else>메시지 전송</span>
          </button>
        </form>

        <div v-else class="chat-locked">
          <p>로그인한 사용자만 채팅에 참여할 수 있습니다. 위에서 먼저 로그인해 주세요.</p>
        </div>
      </section>

      <section v-if="isLoading" class="panel">
        <h2>로딩 중...</h2>
        <p>Postgres에 저장된 메시지를 가져오고 있습니다.</p>
      </section>

      <section v-else>
        <article v-for="message in messages" :key="message.id" class="panel">
          <header>
            <h2>{{ message.title }}</h2>
            <time>{{ formatDate(message.created_at) }}</time>
          </header>
          <p>{{ message.body }}</p>
        </article>

        <div v-if="!messages.length" class="panel empty">
          <p>아직 등록된 메시지가 없습니다. Django Admin에서 새로운 메시지를 추가해 보세요.</p>
        </div>

        <div v-if="errorMessage" class="panel error">
          <p>{{ errorMessage }}</p>
        </div>
      </section>
    </main>

    <footer>
      <strong>GitHub Pages · https://py9245.github.io</strong> 에서 정적 SPA를 제공하며, API는 Django 백엔드에서 제공합니다.
    </footer>
  </div>
</template>
