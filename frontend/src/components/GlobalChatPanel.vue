<script setup>
import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { fetchChatRooms, getApiBaseUrl, joinChatRoom, loadAuthToken } from '@/services/api'
import { useSession } from '@/composables/useSession'

const DEFAULT_ROOM_NAME = '오픈 라운지'
const HISTORY_LIMIT = 80
const RECONNECT_DELAY = 4000

const { profile, ensureProfileLoaded } = useSession()

const globalRoom = ref(null)
const messages = ref([])
const isPreparingRoom = ref(false)
const isSending = ref(false)
const realtimeState = reactive({
  status: 'idle',
  detail: '실시간 연결을 준비 중입니다.',
})
const chatForm = reactive({
  content: '',
  is_anonymous: true,
})
const alerts = reactive({
  error: '',
  info: '',
  form: '',
})

const messageContainer = ref(null)
const wsRef = ref(null)
let reconnectTimer = null
let shouldReconnect = false

const isAdmin = computed(() => Boolean(profile.value?.user?.is_staff))
const canSend = computed(
  () => Boolean(profile.value && globalRoom.value && chatForm.content.trim()) && realtimeState.status === 'open',
)
const profileSummary = computed(() => {
  const user = profile.value?.user
  if (!user) {
    return ''
  }
  const email = user.email || '이메일 정보 없음'
  return `${user.username} 님으로 접속 중입니다. (${email})`
})

const statusMessages = {
  idle: '실시간 연결을 준비 중입니다.',
  connecting: '실시간 연결을 준비 중입니다...',
  open: '실시간 연결됨 · 새 메시지가 자동으로 표시됩니다.',
  closed: '실시간 연결이 끊어졌습니다. 잠시 후 재시도합니다.',
}

const setRealtimeState = (status, detail) => {
  realtimeState.status = status
  realtimeState.detail = detail || statusMessages[status] || ''
}

const resolveWsOrigin = () => {
  if (typeof window === 'undefined') {
    return null
  }
  const runtimeBase = getApiBaseUrl()
  try {
    const absolute = new URL(runtimeBase, window.location.origin)
    const protocol = absolute.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${protocol}//${absolute.host}`
  } catch {
    if (!window.location?.host) {
      return null
    }
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${protocol}//${window.location.host}`
  }
}

const wsOrigin = ref(resolveWsOrigin())

const scrollToBottom = () => {
  nextTick(() => {
    if (!messageContainer.value) return
    messageContainer.value.scrollTop = messageContainer.value.scrollHeight
  })
}

const resetAlerts = () => {
  alerts.error = ''
  alerts.info = ''
  alerts.form = ''
}

const disconnectSocket = () => {
  shouldReconnect = false
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
  if (wsRef.value) {
    try {
      wsRef.value.close()
    } catch {
      // ignore
    }
  }
  wsRef.value = null
  if (!profile.value) {
    setRealtimeState('idle', '로그인 후 실시간 자유 채팅을 이용할 수 있습니다.')
  } else {
    setRealtimeState('idle')
  }
}

const buildWsUrl = () => {
  const token = loadAuthToken()
  if (!token || !globalRoom.value || !wsOrigin.value) {
    return null
  }
  return `${wsOrigin.value}/ws/chatrooms/${globalRoom.value.id}/?token=${encodeURIComponent(token)}`
}

const sendAction = (payload) => {
  if (!wsRef.value || wsRef.value.readyState !== WebSocket.OPEN) {
    alerts.error = '실시간 연결을 준비 중입니다. 잠시 후 다시 시도해주세요.'
    setRealtimeState('connecting')
    return false
  }
  try {
    wsRef.value.send(JSON.stringify(payload))
    return true
  } catch (error) {
    console.error('WebSocket 전송 오류', error)
    alerts.error = '실시간 메시지를 전송하지 못했습니다.'
    return false
  }
}

const refreshHistory = () => {
  alerts.error = ''
  if (!sendAction({ action: 'fetch_history' })) {
    alerts.info = ''
  }
}

const handleSocketMessage = (event) => {
  try {
    const data = JSON.parse(event.data)
    if (data.event === 'history') {
      messages.value = Array.isArray(data.messages) ? data.messages.slice(-HISTORY_LIMIT) : []
      scrollToBottom()
      alerts.info = ''
    } else if (data.event === 'message') {
      if (data.message) {
        messages.value = [...messages.value, data.message].slice(-HISTORY_LIMIT)
        scrollToBottom()
      }
    } else if (data.event === 'error') {
      alerts.error = data.detail || '실시간 채팅 오류가 발생했습니다.'
    }
  } catch (error) {
    console.error('WebSocket 메시지 파싱 실패', error)
  }
}

const connectSocket = () => {
  if (!profile.value || !globalRoom.value) {
    disconnectSocket()
    return
  }
  const url = buildWsUrl()
  if (!url) {
    alerts.error = '실시간 연결 정보를 계산하지 못했습니다.'
    return
  }
  disconnectSocket()
  shouldReconnect = true
  setRealtimeState('connecting')
  wsRef.value = new WebSocket(url)
  wsRef.value.addEventListener('open', () => {
    setRealtimeState('open')
    alerts.info = '실시간 연결이 완료되었습니다.'
    refreshHistory()
  })
  wsRef.value.addEventListener('message', handleSocketMessage)
  wsRef.value.addEventListener('close', () => {
    wsRef.value = null
    if (shouldReconnect && profile.value && globalRoom.value) {
      setRealtimeState('closed')
      reconnectTimer = window.setTimeout(() => {
        reconnectTimer = null
        connectSocket()
      }, RECONNECT_DELAY)
    } else {
      setRealtimeState('idle')
    }
  })
  wsRef.value.addEventListener('error', (event) => {
    console.error('WebSocket error', event)
    alerts.error = '실시간 연결 중 문제가 발생했습니다.'
  })
}

const ensureDefaultRoom = async () => {
  const payload = await fetchChatRooms()
  const rooms = Array.isArray(payload?.rooms) ? payload.rooms : []
  if (!rooms.length) {
    throw new Error('입장 가능한 공개 채팅방이 없습니다.')
  }
  let target =
    rooms.find((room) => room.name === DEFAULT_ROOM_NAME) || rooms.find((room) => !room.is_private) || rooms[0]
  if (!target) {
    throw new Error('입장 가능한 공개 채팅방이 없습니다.')
  }
  if (!target.is_member) {
    const joinPayload = await joinChatRoom({ name: target.name })
    target = joinPayload?.room || target
  }
  return target
}

const prepareRoom = async () => {
  if (!profile.value) {
    disconnectSocket()
    return
  }
  isPreparingRoom.value = true
  alerts.error = ''
  alerts.info = ''
  try {
    const room = await ensureDefaultRoom()
    globalRoom.value = room
    messages.value = []
    connectSocket()
  } catch (error) {
    console.error(error)
    globalRoom.value = null
    alerts.error = error?.message || '채팅방 정보를 불러오지 못했습니다.'
  } finally {
    isPreparingRoom.value = false
  }
}

const handleSubmit = () => {
  alerts.form = ''
  if (!profile.value) {
    alerts.form = '로그인 후 이용해 주세요.'
    return
  }
  if (!globalRoom.value) {
    alerts.form = '입장 가능한 공개 채팅방이 없습니다.'
    return
  }
  const content = chatForm.content.trim()
  if (!content) {
    alerts.form = '메시지를 입력해 주세요.'
    return
  }
  const payload = {
    action: 'send_message',
    content,
    is_anonymous: !isAdmin.value ? chatForm.is_anonymous : false,
  }
  isSending.value = true
  if (sendAction(payload)) {
    chatForm.content = ''
  }
  isSending.value = false
}

const handleTextareaKeydown = (event) => {
  if (event.key !== 'Enter' || event.shiftKey || event.isComposing) {
    return
  }
  event.preventDefault()
  handleSubmit()
}

watch(
  profile,
  (value, previous) => {
    if (!value) {
      chatForm.content = ''
      chatForm.is_anonymous = true
      globalRoom.value = null
      messages.value = []
      disconnectSocket()
      setRealtimeState('idle', '로그인 후 실시간 자유 채팅을 이용할 수 있습니다.')
    } else if (!previous) {
      chatForm.is_anonymous = !isAdmin.value
      prepareRoom()
    }
  },
  { immediate: false },
)

watch(
  isAdmin,
  (current) => {
    if (current) {
      chatForm.is_anonymous = false
    }
  },
  { immediate: true },
)

watch(messages, scrollToBottom)

onMounted(async () => {
  await ensureProfileLoaded()
  if (profile.value) {
    chatForm.is_anonymous = !isAdmin.value
    await prepareRoom()
  } else {
    setRealtimeState('idle', '로그인 후 실시간 자유 채팅을 이용할 수 있습니다.')
  }
})

onUnmounted(() => {
  disconnectSocket()
})
</script>

<template>
  <div class="card border-0">
    <div class="card-body">
      <div class="d-flex flex-column flex-lg-row justify-content-between gap-3 mb-3">
        <div>
          <h5 class="text-light mb-1">실시간 자유 채팅</h5>
          <p class="text-white-50 mb-0">
            누구나 참여할 수 있는 공개 채팅방입니다. 새 메시지는 실시간으로 표시됩니다.
          </p>
          <p class="text-white-50 small mb-0">
            {{ globalRoom ? `${globalRoom.name} · 정원 ${globalRoom.member_count}/${globalRoom.capacity}` : '채팅방 준비 중' }}
          </p>
          <p class="text-white-50 small mb-0">{{ realtimeState.detail }}</p>
        </div>
        <div class="d-flex gap-2 align-items-start">
          <button class="btn btn-outline-info nav-hover" :disabled="isPreparingRoom" type="button" @click="prepareRoom">
            <span v-if="isPreparingRoom">준비 중...</span>
            <span v-else>다시 연결</span>
          </button>
          <button class="btn btn-outline-light nav-hover" type="button" @click="refreshHistory">즉시 새로고침</button>
        </div>
      </div>

      <div v-if="alerts.error" class="alert alert-danger">{{ alerts.error }}</div>
      <div v-else-if="alerts.info" class="alert alert-success">{{ alerts.info }}</div>

      <div
        ref="messageContainer"
        class="chat-messages list-group list-group-flush mb-3"
        style="max-height: 420px; overflow-y: auto"
      >
        <p v-if="!messages.length" class="text-center text-white-50 my-5">아직 대화가 없습니다. 첫 메시지를 남겨보세요!</p>
        <article v-for="message in messages" :key="message.id" class="list-group-item bg-transparent text-light">
          <div class="d-flex justify-content-between align-items-center">
            <span class="fw-semibold" :class="{ 'text-warning': message.is_anonymous }">
              {{ message.display_name || (message.is_anonymous ? '익명' : '사용자') }}
            </span>
            <small>{{ new Date(message.created_at).toLocaleString('ko-KR', { dateStyle: 'short', timeStyle: 'short' }) }}</small>
          </div>
          <p class="mb-0 mt-1">{{ message.content }}</p>
        </article>
      </div>

      <div v-if="!profile" class="alert alert-warning mb-0">
        로그인한 사용자만 자유 채팅에 참여할 수 있습니다. 계정 페이지에서 로그인해 주세요.
      </div>
      <div v-else>
        <div class="alert alert-info mb-3">{{ profileSummary }}</div>
        <form autocomplete="off" @submit.prevent="handleSubmit">
          <div v-if="!isAdmin" class="form-check form-switch mb-3">
            <input id="globalChatAnon" v-model="chatForm.is_anonymous" class="form-check-input" type="checkbox" />
            <label class="form-check-label text-white-50" for="globalChatAnon">
              {{ chatForm.is_anonymous ? '익명으로 보내기' : '아이디 공개' }}
            </label>
          </div>
          <p v-else class="text-white-50 small">관리자는 실명(아이디)으로만 메시지를 보낼 수 있습니다.</p>

          <textarea
            v-model="chatForm.content"
            class="form-control"
            placeholder="지금 떠오르는 이야기를 적어보세요 (최대 500자)"
            maxlength="500"
            rows="4"
            @keydown="handleTextareaKeydown"
          ></textarea>
          <div v-if="alerts.form" class="alert alert-warning mt-2">{{ alerts.form }}</div>
          <button class="btn btn-primary nav-hover mt-3" :disabled="isSending || !canSend" type="submit">
            <span v-if="isSending">전송 중...</span>
            <span v-else>메시지 전송</span>
          </button>
        </form>
      </div>
    </div>
  </div>
</template>
