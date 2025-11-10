<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { fetchChatMessages, postChatMessage } from '@/services/api'
import { useSession } from '@/composables/useSession'

const { profile, ensureProfileLoaded } = useSession()

const chatMessages = ref([])
const chatForm = reactive({ content: '', is_anonymous: true })
const isLoading = ref(false)
const isSending = ref(false)
const chatError = ref('')
const CHAT_HISTORY_LIMIT = 80
const CHAT_POLL_INTERVAL = 500
let pollTimer = null

const formatDate = (value) => {
  if (!value) return ''
  const date = typeof value === 'string' ? new Date(value) : value
  if (Number.isNaN(date.getTime())) return ''
  return new Intl.DateTimeFormat('ko-KR', { dateStyle: 'short', timeStyle: 'short' }).format(date)
}

const canSend = computed(() => Boolean(profile.value && chatForm.content.trim()))

const loadMessages = async ({ silent = false } = {}) => {
  if (!silent) {
    isLoading.value = true
    chatError.value = ''
  }
  try {
    const payload = await fetchChatMessages({ limit: CHAT_HISTORY_LIMIT })
    chatMessages.value = Array.isArray(payload?.messages) ? payload.messages : []
  } catch (error) {
    console.error(error)
    chatError.value = '채팅 메시지를 불러오지 못했습니다.'
  } finally {
    if (!silent) {
      isLoading.value = false
    }
  }
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const startPolling = () => {
  stopPolling()
  pollTimer = window.setInterval(() => {
    loadMessages({ silent: true })
  }, CHAT_POLL_INTERVAL)
}

const handleSubmit = async () => {
  if (!profile.value) {
    chatError.value = '로그인 후 이용해 주세요.'
    return
  }
  const content = chatForm.content.trim()
  if (!content) {
    chatError.value = '메시지를 입력해 주세요.'
    return
  }
  isSending.value = true
  try {
    const payload = await postChatMessage({
      content,
      is_anonymous: chatForm.is_anonymous,
    })
    chatMessages.value = [...chatMessages.value, payload].slice(-CHAT_HISTORY_LIMIT)
    chatForm.content = ''
    chatError.value = ''
  } catch (error) {
    console.error(error)
    chatError.value = error?.payload?.detail || '메시지를 전송하지 못했습니다.'
  } finally {
    isSending.value = false
  }
}

onMounted(async () => {
  await ensureProfileLoaded()
  await loadMessages()
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<template>
  <section class="panel">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <div>
        <h2 class="h4 text-light mb-1">실시간 자유 채팅방</h2>
        <p class="text-white-50 mb-0">0.5초마다 최신 메시지를 불러옵니다.</p>
      </div>
      <router-link class="btn btn-outline-light nav-hover" to="/boards">게시판 보기</router-link>
    </div>

    <div v-if="isLoading" class="alert alert-info">채팅 메시지를 불러오는 중...</div>
    <div v-else-if="!chatMessages.length" class="alert alert-secondary">아직 대화가 없습니다. 첫 메시지를 남겨보세요!</div>
    <div v-else class="chat-messages list-group list-group-flush">
      <article v-for="chat in chatMessages" :key="chat.id" class="chat-message list-group-item">
        <div class="d-flex justify-content-between">
          <span class="fw-semibold" :class="{ 'text-warning': chat.is_anonymous }">{{ chat.display_name }}</span>
          <small>{{ formatDate(chat.created_at) }}</small>
        </div>
        <p class="mt-1">{{ chat.content }}</p>
      </article>
    </div>

    <div v-if="chatError" class="alert alert-danger mt-4">{{ chatError }}</div>

    <form v-if="profile" class="chat-form mt-4" autocomplete="off" @submit.prevent="handleSubmit">
      <div class="form-check form-switch mb-3">
        <input id="chatAnon" v-model="chatForm.is_anonymous" class="form-check-input" type="checkbox" />
        <label class="form-check-label text-white-50" for="chatAnon">
          {{ chatForm.is_anonymous ? '익명으로 보내기' : '아이디 공개' }}
        </label>
      </div>
      <textarea
        v-model="chatForm.content"
        class="form-control"
        name="chat-content"
        placeholder="지금 떠오르는 생각을 적어보세요 (최대 500자)"
        maxlength="500"
      ></textarea>
      <button class="btn btn-primary nav-hover mt-3" :disabled="isSending || !canSend" type="submit">
        <span v-if="isSending">전송 중...</span>
        <span v-else>메시지 전송</span>
      </button>
    </form>

    <div v-else class="alert alert-warning mt-4">
      로그인한 사용자만 채팅에 참여할 수 있습니다. 계정 페이지에서 로그인해 주세요.
    </div>
  </section>
</template>
