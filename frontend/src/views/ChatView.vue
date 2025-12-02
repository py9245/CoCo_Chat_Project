<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { createChatRoom, fetchChatRooms, getApiBaseUrl, joinChatRoom, leaveChatRoom, loadAuthToken } from '@/services/api'
import { useSession } from '@/composables/useSession'
import GlobalChatPanel from '@/components/GlobalChatPanel.vue'

const { profile, ensureProfileLoaded } = useSession()
const isAdmin = computed(() => Boolean(profile.value?.user?.is_staff))

const rooms = ref([])
const roomsLoading = ref(false)
const roomsError = ref('')
const currentRoom = ref(null)
const joiningRoomId = ref(null)
const leavingRoom = ref(false)
const chatMessages = ref([])
const chatForm = reactive({ content: '', is_anonymous: true })
const isLoadingMessages = ref(false)
const isSending = ref(false)
const chatError = ref('')
const realtimeState = reactive({
  status: 'idle', // idle | connecting | open | closed
  error: '',
})
const createRoomForm = reactive({ name: '', capacity: 10, is_private: false, password: '' })
const createRoomLoading = ref(false)
const privateJoinForm = reactive({ name: '', password: '' })
const privateJoinLoading = ref(false)
const CHAT_HISTORY_LIMIT = 80
let reconnectTimer = null
let shouldReconnect = false
const ws = ref(null)
const canUseAnonymous = computed(() => !isAdmin.value)
const activeTab = ref('global')
const realtimeLabel = computed(() => {
  switch (realtimeState.status) {
    case 'open':
      return '실시간 연결됨'
    case 'connecting':
      return '연결 준비 중'
    case 'closed':
      return '재연결 대기'
    default:
      return '대기 중'
  }
})
const connectionToneClass = computed(() => {
  if (realtimeState.status === 'open') return 'pill-success'
  if (realtimeState.status === 'connecting') return 'pill-warning'
  if (realtimeState.status === 'closed') return 'pill-danger'
  return 'pill-muted'
})
const currentRoomSummary = computed(() => {
  if (!currentRoom.value) {
    return '입장 후 메시지를 보낼 수 있습니다.'
  }
  return `정원 ${currentRoom.value.member_count}/${currentRoom.value.capacity} · ${currentRoom.value.is_private ? '비공개' : '공개'}`
})

const formatDate = (value) => {
  if (!value) return ''
  const date = typeof value === 'string' ? new Date(value) : value
  if (Number.isNaN(date.getTime())) return ''
  return new Intl.DateTimeFormat('ko-KR', { dateStyle: 'short', timeStyle: 'short' }).format(date)
}

const canSend = computed(
  () =>
    Boolean(profile.value && currentRoom.value && chatForm.content.trim()) && realtimeState.status === 'open',
)

const loadRooms = async () => {
  roomsLoading.value = true
  roomsError.value = ''
  try {
    const payload = await fetchChatRooms()
    rooms.value = Array.isArray(payload?.rooms) ? payload.rooms : []
  } catch (error) {
    console.error(error)
    roomsError.value = '채팅방 목록을 불러오지 못했습니다.'
  } finally {
    roomsLoading.value = false
  }
}

const setCurrentRoom = (room) => {
  currentRoom.value = room || null
}

const resolveWsOrigin = () => {
  if (typeof window === 'undefined') return null
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

const wsOrigin = resolveWsOrigin()

const buildChatWsUrl = (roomId) => {
  const token = loadAuthToken()
  if (!token || !wsOrigin) {
    return null
  }
  return `${wsOrigin}/ws/chatrooms/${roomId}/?token=${encodeURIComponent(token)}`
}

const clearReconnectTimer = () => {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
}

const disconnectSocket = () => {
  shouldReconnect = false
  clearReconnectTimer()
  if (ws.value) {
    try {
      ws.value.close()
    } catch {
      // ignore
    }
  }
  ws.value = null
  if (currentRoom.value) {
    realtimeState.status = 'closed'
  } else {
    realtimeState.status = 'idle'
  }
}

const scheduleReconnect = () => {
  if (!shouldReconnect || reconnectTimer) return
  reconnectTimer = window.setTimeout(() => {
    reconnectTimer = null
    if (currentRoom.value) {
      connectSocket(currentRoom.value.id)
    }
  }, 3000)
}

const connectSocket = (roomId) => {
  disconnectSocket()
  if (!roomId) return
  const url = buildChatWsUrl(roomId)
  if (!url) {
    chatError.value = '로그인 후 이용해 주세요.'
    return
  }
  shouldReconnect = true
  realtimeState.status = 'connecting'
  realtimeState.error = ''
  isLoadingMessages.value = true
  const socket = new WebSocket(url)
  ws.value = socket

  socket.addEventListener('open', () => {
    realtimeState.status = 'open'
    realtimeState.error = ''
    socket.send(JSON.stringify({ action: 'fetch_history' }))
  })

  socket.addEventListener('message', (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.event === 'history') {
        chatMessages.value = Array.isArray(data.messages) ? data.messages.slice(-CHAT_HISTORY_LIMIT) : []
        isLoadingMessages.value = false
      } else if (data.event === 'message') {
        const message = data.message
        if (message) {
          chatMessages.value = [...chatMessages.value, message].slice(-CHAT_HISTORY_LIMIT)
        }
      } else if (data.event === 'error') {
        chatError.value = data.detail || '실시간 채팅 오류가 발생했습니다.'
      }
    } catch (error) {
      console.error('WebSocket message parse error', error)
    }
  })

  socket.addEventListener('close', () => {
    ws.value = null
    if (shouldReconnect && currentRoom.value) {
      realtimeState.status = 'closed'
      scheduleReconnect()
    } else {
      realtimeState.status = currentRoom.value ? 'closed' : 'idle'
    }
  })

  socket.addEventListener('error', (event) => {
    console.error('WebSocket error', event)
    realtimeState.error = '실시간 연결에 문제가 발생했습니다.'
  })
}

watch(
  isAdmin,
  (current) => {
    if (current) {
      chatForm.is_anonymous = false
    }
  },
  { immediate: true },
)

watch(currentRoom, (room) => {
  chatMessages.value = []
  chatError.value = ''
  if (room) {
    connectSocket(room.id)
  } else {
    disconnectSocket()
    isLoadingMessages.value = false
  }
})

const requireLogin = () => {
  if (!profile.value) {
    chatError.value = '로그인 후 이용해 주세요.'
    return false
  }
  return true
}

const handleSelectRoom = async (room) => {
  if (!requireLogin()) return
  joiningRoomId.value = room.id
  chatError.value = ''
  try {
    const payload = await joinChatRoom({ name: room.name })
    setCurrentRoom(payload?.room ?? null)
    if (!room.is_private) {
      await loadRooms()
    }
  } catch (error) {
    console.error(error)
    chatError.value = error?.payload?.detail || '채팅방에 입장하지 못했습니다.'
  } finally {
    joiningRoomId.value = null
  }
}

const handleJoinPrivateRoom = async () => {
  if (!requireLogin()) return
  if (!privateJoinForm.name.trim()) {
    chatError.value = '비공개 채팅방 이름을 입력해주세요.'
    return
  }
  if (!privateJoinForm.password.trim()) {
    chatError.value = '비공개 채팅방 비밀번호를 입력해주세요.'
    return
  }
  privateJoinLoading.value = true
  chatError.value = ''
  try {
    const payload = await joinChatRoom({
      name: privateJoinForm.name.trim(),
      password: privateJoinForm.password,
    })
    setCurrentRoom(payload?.room ?? null)
    privateJoinForm.name = ''
    privateJoinForm.password = ''
  } catch (error) {
    console.error(error)
    chatError.value = error?.payload?.detail || '비공개 채팅방에 입장하지 못했습니다.'
  } finally {
    privateJoinLoading.value = false
  }
}

const handleCreateRoom = async () => {
  if (!requireLogin()) return
  createRoomLoading.value = true
  chatError.value = ''
  try {
    const payload = await createChatRoom({
      name: createRoomForm.name.trim(),
      capacity: Number(createRoomForm.capacity),
      is_private: createRoomForm.is_private,
      password: createRoomForm.is_private ? createRoomForm.password : '',
    })
    if (!payload?.room) {
      throw new Error('채팅방 응답이 없습니다.')
    }
    setCurrentRoom(payload.room)
    if (!payload.room.is_private) {
      await loadRooms()
    }
    createRoomForm.name = ''
    createRoomForm.password = ''
    createRoomForm.capacity = 10
    createRoomForm.is_private = false
  } catch (error) {
    console.error(error)
    chatError.value =
      error?.payload?.detail ||
      (error?.payload && typeof error.payload === 'object'
        ? Object.values(error.payload).flat().join(' ')
        : '채팅방을 생성하지 못했습니다.')
  } finally {
    createRoomLoading.value = false
  }
}

const handleLeaveRoom = async () => {
  if (!currentRoom.value || !requireLogin()) return
  leavingRoom.value = true
  chatError.value = ''
  try {
    await leaveChatRoom(currentRoom.value.id)
    disconnectSocket()
    setCurrentRoom(null)
    await loadRooms()
  } catch (error) {
    console.error(error)
    chatError.value = error?.payload?.detail || '채팅방에서 나가지 못했습니다.'
  } finally {
    leavingRoom.value = false
  }
}

const handleSubmit = () => {
  if (!requireLogin()) return
  if (!currentRoom.value) {
    chatError.value = '먼저 채팅방에 입장해 주세요.'
    return
  }
  if (realtimeState.status !== 'open' || !ws.value) {
    chatError.value = '실시간 연결을 준비 중입니다. 잠시 후 다시 시도해 주세요.'
    if (currentRoom.value) {
      connectSocket(currentRoom.value.id)
    }
    return
  }
  const content = chatForm.content.trim()
  if (!content) {
    chatError.value = '메시지를 입력해 주세요.'
    return
  }
  isSending.value = true
  const payload = {
    action: 'send_message',
    content,
    is_anonymous: canUseAnonymous.value ? chatForm.is_anonymous : false,
  }
  try {
    ws.value.send(JSON.stringify(payload))
    chatForm.content = ''
    chatError.value = ''
  } catch (error) {
    console.error(error)
    chatError.value = '메시지를 전송하지 못했습니다.'
  } finally {
    isSending.value = false
  }
}

const handleEditorKeydown = (event) => {
  if (event.key !== 'Enter' || event.shiftKey || event.isComposing) {
    return
  }
  event.preventDefault()
  handleSubmit()
}

onMounted(async () => {
  await ensureProfileLoaded()
  await loadRooms()
})

onUnmounted(() => {
  disconnectSocket()
})
</script>

<template>
  <section class="panel">
    <div class="d-flex flex-column flex-lg-row justify-content-between align-items-start gap-3 mb-4">
      <div>
        <div class="d-flex align-items-center gap-2 mb-2">
          <span class="pill pill-muted">오픈 채팅</span>
          <span class="pill" :class="connectionToneClass">{{ realtimeLabel }}</span>
        </div>
        <h2 class="h4 text-light mb-1">누구나 참여하는 오픈 라운지</h2>
        <p class="text-white-50 mb-0">
          원하는 방을 선택해 바로 대화하거나, 새 방을 만들어 초대 코드를 공유하세요.
        </p>
      </div>
      <div class="d-flex flex-wrap gap-2">
        <router-link class="btn btn-outline-light nav-hover" to="/">메인으로</router-link>
        <button class="btn btn-outline-info nav-hover" type="button" @click="loadRooms">목록 새로고침</button>
      </div>
    </div>

    <div class="row g-3 mb-4">
      <div class="col-12 col-lg-4">
        <div class="soft-card h-100">
          <p class="text-white-50 small mb-1">내 상태</p>
          <h6 class="mb-1 text-light">{{ profile ? profile.user.username : '로그인 필요' }}</h6>
          <p class="text-white-50 mb-0">
            {{ profile ? (canUseAnonymous ? '익명/닉네임 선택 가능' : '관리자 · 실명 발송') : '로그인 후 참여 가능' }}
          </p>
        </div>
      </div>
      <div class="col-12 col-lg-4">
        <div class="soft-card h-100">
          <p class="text-white-50 small mb-1">실시간 연결</p>
          <div class="d-flex align-items-center gap-2">
            <span class="pill" :class="connectionToneClass">{{ realtimeLabel }}</span>
            <small class="text-white-50">{{ realtimeState.error || '끊기면 자동으로 다시 연결합니다.' }}</small>
          </div>
        </div>
      </div>
      <div class="col-12 col-lg-4">
        <div class="soft-card h-100">
          <p class="text-white-50 small mb-1">현재 방</p>
          <strong class="d-block mb-1 text-light">{{ currentRoom ? currentRoom.name : '아직 선택되지 않음' }}</strong>
          <small class="text-white-50">{{ currentRoomSummary }}</small>
        </div>
      </div>
    </div>

    <div class="nav nav-pills gap-2 mb-4 flex-wrap">
      <button
        class="btn nav-hover"
        :class="activeTab === 'global' ? 'btn-primary' : 'btn-outline-light'"
        type="button"
        @click="activeTab = 'global'"
      >
        실시간 자유 채팅
      </button>
      <button
        class="btn nav-hover"
        :class="activeTab === 'rooms' ? 'btn-primary' : 'btn-outline-light'"
        type="button"
        @click="activeTab = 'rooms'"
      >
        채팅방 관리
      </button>
    </div>
    <div v-if="activeTab === 'global'">
      <GlobalChatPanel />
    </div>
    <div v-else>
      <div class="alert alert-info mb-4">
        원하는 분위기의 방이 없다면 직접 만들고 링크를 공유하세요. 비공개 방은 목록에 표시되지 않고 비밀번호로만 입장합니다.
      </div>

      <div class="row g-4">
        <div class="col-12 col-lg-4">
          <div class="card border-0 mb-4">
            <div class="card-body">
              <div class="d-flex justify-content-between align-items-center mb-2">
                <h5 class="text-light mb-0">공개 채팅방</h5>
                <button class="btn btn-sm btn-outline-info nav-hover" type="button" @click="loadRooms">새로고침</button>
              </div>
              <p class="text-white-50 small mb-3">목록에는 누구나 입장 가능한 공개형 채팅방만 표시됩니다.</p>
              <div v-if="roomsLoading" class="alert alert-info">채팅방 목록을 불러오는 중...</div>
              <div v-else-if="roomsError" class="alert alert-danger">{{ roomsError }}</div>
              <div v-else class="d-flex flex-column gap-2 room-list">
                <div v-if="!rooms.length" class="panel-placeholder">아직 공개 채팅방이 없습니다.</div>
                <article
                  v-for="room in rooms"
                  :key="room.id"
                  class="room-tile d-flex justify-content-between align-items-center"
                >
                  <div>
                    <p class="mb-0 fw-semibold text-light">{{ room.name }}</p>
                    <small class="text-white-50">
                      {{ room.member_count }}/{{ room.capacity }} · {{ room.owner_username || '운영자' }}
                    </small>
                  </div>
                  <button
                    class="btn btn-sm nav-hover"
                    :class="room.is_member ? 'btn-secondary' : 'btn-outline-light'"
                    :disabled="
                      joiningRoomId === room.id ||
                      room.member_count >= room.capacity ||
                      (room.is_member && currentRoom && currentRoom.id === room.id)
                    "
                    type="button"
                    @click="handleSelectRoom(room)"
                  >
                    <span v-if="joiningRoomId === room.id">입장 중...</span>
                    <span v-else-if="room.is_member && currentRoom && currentRoom.id === room.id">이용 중</span>
                    <span v-else-if="room.is_member">입장 완료</span>
                    <span v-else-if="room.member_count >= room.capacity">정원 초과</span>
                    <span v-else>입장</span>
                  </button>
                </article>
              </div>
            </div>
          </div>

          <div class="card border-0 mb-4">
            <div class="card-body">
              <h5 class="text-light mb-3">채팅방 생성</h5>
              <form class="row g-3" autocomplete="off" @submit.prevent="handleCreateRoom">
                <div class="col-12">
                  <label class="form-label text-white-50">채팅방 이름</label>
                  <input v-model="createRoomForm.name" class="form-control" maxlength="50" placeholder="예) 주말 영화 추천방" required />
                </div>
                <div class="col-12">
                  <label class="form-label text-white-50">정원 (2~200명)</label>
                  <input
                    v-model.number="createRoomForm.capacity"
                    class="form-control"
                    min="2"
                    max="200"
                    type="number"
                    required
                  />
                </div>
                <div class="col-12 form-check form-switch">
                  <input id="createPrivate" v-model="createRoomForm.is_private" class="form-check-input" type="checkbox" />
                  <label class="form-check-label text-white-50" for="createPrivate">비공개 채팅방</label>
                </div>
                <div v-if="createRoomForm.is_private" class="col-12">
                  <label class="form-label text-white-50">비밀번호</label>
                  <input v-model="createRoomForm.password" class="form-control" type="password" minlength="4" required />
                  <small class="text-white-50">목록에 표시되지 않으며 비밀번호로만 입장합니다.</small>
                </div>
                <div class="col-12">
                  <button class="btn btn-primary nav-hover w-100" :disabled="createRoomLoading" type="submit">
                    <span v-if="createRoomLoading">생성 중...</span>
                    <span v-else>채팅방 생성</span>
                  </button>
                </div>
              </form>
            </div>
          </div>

          <div class="card border-0">
            <div class="card-body">
              <h5 class="text-light mb-3">비공개 채팅방 입장</h5>
              <form class="row g-3" autocomplete="off" @submit.prevent="handleJoinPrivateRoom">
                <div class="col-12">
                  <label class="form-label text-white-50">채팅방 이름</label>
                  <input v-model="privateJoinForm.name" class="form-control" placeholder="예) 프로젝트 A" required />
                </div>
                <div class="col-12">
                  <label class="form-label text-white-50">비밀번호</label>
                  <input v-model="privateJoinForm.password" class="form-control" type="password" required />
                </div>
                <div class="col-12">
                  <button class="btn btn-outline-light nav-hover w-100" :disabled="privateJoinLoading" type="submit">
                    <span v-if="privateJoinLoading">입장 중...</span>
                    <span v-else>입장하기</span>
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>

        <div class="col-12 col-lg-8">
          <div class="card border-0 h-100 chat-frame">
            <div class="card-body d-flex flex-column gap-3 h-100">
              <div class="d-flex justify-content-between align-items-start flex-wrap gap-2">
                <div>
                  <h5 class="text-light mb-1">{{ currentRoom ? currentRoom.name : '채팅방을 선택해 주세요' }}</h5>
                  <p class="text-white-50 mb-0">
                    {{ currentRoom ? currentRoomSummary : '좌측에서 채팅방을 선택하거나 새로 만들 수 있습니다.' }}
                  </p>
                  <p v-if="currentRoom" class="text-white-50 small mb-0">
                    {{ realtimeLabel }} · 끊기면 자동으로 재연결합니다.
                  </p>
                </div>
                <div class="d-flex gap-2">
                  <router-link class="btn btn-outline-light btn-sm nav-hover" to="/boards">게시판 보기</router-link>
                  <button
                    v-if="currentRoom"
                    class="btn btn-outline-danger btn-sm nav-hover"
                    :disabled="leavingRoom"
                    type="button"
                    @click="handleLeaveRoom"
                  >
                    <span v-if="leavingRoom">나가는 중...</span>
                    <span v-else>채팅방 나가기</span>
                  </button>
                </div>
              </div>

              <div v-if="isLoadingMessages" class="alert alert-info">채팅 메시지를 불러오는 중...</div>
              <div v-else-if="currentRoom && !chatMessages.length" class="alert alert-secondary">
                아직 대화가 없습니다. 첫 메시지를 남겨보세요!
              </div>
              <div v-else-if="currentRoom" class="chat-messages list-group list-group-flush">
                <article 
                  v-for="chat in chatMessages" 
                  :key="chat.id" 
                  class="chat-message list-group-item border-0 bg-transparent px-0"
                  :class="{ 'text-end': profile && chat.username === profile.user.username }"
                >
                  <div class="d-inline-block text-start" style="max-width: 80%;">
                    <div class="d-flex align-items-end gap-2 mb-1" :class="{ 'justify-content-end': profile && chat.username === profile.user.username }">
                      <small v-if="profile && chat.username === profile.user.username" class="text-muted">{{ formatDate(chat.created_at) }}</small>
                      <span class="fw-semibold badge bg-light text-dark border" v-if="!(profile && chat.username === profile.user.username)" :class="{ 'text-warning': chat.is_anonymous }">
                        {{ chat.display_name }}
                      </span>
                      <small v-if="!(profile && chat.username === profile.user.username)" class="text-muted">{{ formatDate(chat.created_at) }}</small>
                    </div>
                    <div 
                      class="p-3 rounded-3 shadow-sm"
                      :class="[
                        profile && chat.username === profile.user.username 
                          ? 'bg-primary text-white fw-bold rounded-top-right-0' 
                          : 'bg-white border fw-normal rounded-top-left-0'
                      ]"
                    >
                      {{ chat.content }}
                    </div>
                  </div>
                </article>
              </div>
              <div v-else class="alert alert-warning">채팅방을 선택하거나 새로 만들어주세요.</div>

              <div v-if="chatError" class="alert alert-danger">{{ chatError }}</div>
              <div v-else-if="realtimeState.error" class="alert alert-warning">{{ realtimeState.error }}</div>

              <form
                v-if="profile && currentRoom"
                class="chat-form mt-auto"
                autocomplete="off"
                @submit.prevent="handleSubmit"
              >
                <div v-if="!isAdmin" class="form-check form-switch mb-3">
                  <input id="chatAnon" v-model="chatForm.is_anonymous" class="form-check-input" type="checkbox" />
                  <label class="form-check-label text-white-50" for="chatAnon">
                    {{ chatForm.is_anonymous ? '익명으로 보내기' : '아이디 공개' }}
                  </label>
                </div>
                <p v-else class="text-white-50 small">관리자는 실명(아이디)으로만 메시지를 보낼 수 있습니다.</p>
                <textarea
                  v-model="chatForm.content"
                  class="form-control"
                  name="chat-content"
                  placeholder="지금 떠오르는 생각을 적어보세요 (최대 500자)"
                  maxlength="500"
                  @keydown="handleEditorKeydown"
                ></textarea>
                <button class="btn btn-primary nav-hover mt-3" :disabled="isSending || !canSend" type="submit">
                  <span v-if="isSending">전송 중...</span>
                  <span v-else>메시지 전송</span>
                </button>
              </form>

              <div v-else-if="profile" class="alert alert-info mt-auto">
                채팅방에 입장해야 메시지를 보낼 수 있습니다.
              </div>
              <div v-else class="alert alert-warning mt-auto">
                로그인한 사용자만 채팅에 참여할 수 있습니다. 계정 페이지에서 로그인해 주세요.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
