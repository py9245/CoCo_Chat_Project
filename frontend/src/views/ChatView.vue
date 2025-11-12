<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import {
  createChatRoom,
  fetchChatMessages,
  fetchChatRooms,
  joinChatRoom,
  leaveChatRoom,
  postChatMessage,
} from '@/services/api'
import { useSession } from '@/composables/useSession'

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
const createRoomForm = reactive({ name: '', capacity: 10, is_private: false, password: '' })
const createRoomLoading = ref(false)
const privateJoinForm = reactive({ name: '', password: '' })
const privateJoinLoading = ref(false)
const CHAT_HISTORY_LIMIT = 80
const CHAT_POLL_INTERVAL = 500
let pollTimer = null
const canUseAnonymous = computed(() => !isAdmin.value)

const formatDate = (value) => {
  if (!value) return ''
  const date = typeof value === 'string' ? new Date(value) : value
  if (Number.isNaN(date.getTime())) return ''
  return new Intl.DateTimeFormat('ko-KR', { dateStyle: 'short', timeStyle: 'short' }).format(date)
}

const canSend = computed(() => Boolean(profile.value && currentRoom.value && chatForm.content.trim()))

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

const loadMessages = async ({ roomId = currentRoom.value?.id, silent = false } = {}) => {
  if (!roomId) return
  if (!silent) {
    isLoadingMessages.value = true
    chatError.value = ''
  }
  try {
    const payload = await fetchChatMessages(roomId, { limit: CHAT_HISTORY_LIMIT })
    chatMessages.value = Array.isArray(payload?.messages) ? payload.messages : []
  } catch (error) {
    console.error(error)
    chatError.value = error?.payload?.detail || '채팅 메시지를 불러오지 못했습니다.'
  } finally {
    if (!silent) {
      isLoadingMessages.value = false
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
  if (!currentRoom.value) return
  pollTimer = window.setInterval(() => {
    loadMessages({ roomId: currentRoom.value?.id, silent: true })
  }, CHAT_POLL_INTERVAL)
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
  stopPolling()
  chatMessages.value = []
  if (room) {
    loadMessages({ roomId: room.id })
    startPolling()
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
    setCurrentRoom(null)
    await loadRooms()
  } catch (error) {
    console.error(error)
    chatError.value = error?.payload?.detail || '채팅방에서 나가지 못했습니다.'
  } finally {
    leavingRoom.value = false
  }
}

const handleSubmit = async () => {
  if (!requireLogin()) return
  if (!currentRoom.value) {
    chatError.value = '먼저 채팅방에 입장해 주세요.'
    return
  }
  const content = chatForm.content.trim()
  if (!content) {
    chatError.value = '메시지를 입력해 주세요.'
    return
  }
  isSending.value = true
  try {
    const payload = await postChatMessage(currentRoom.value.id, {
      content,
      is_anonymous: canUseAnonymous.value ? chatForm.is_anonymous : false,
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
  await loadRooms()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<template>
  <section class="panel">
    <div class="row g-4">
      <div class="col-12 col-lg-4">
        <div class="card border-0 mb-4">
          <div class="card-body">
            <h5 class="text-light mb-3">공개 채팅방</h5>
            <p class="text-white-50 small mb-3">목록에는 누구나 입장 가능한 공개형 채팅방만 표시됩니다.</p>
            <div v-if="roomsLoading" class="alert alert-info">채팅방 목록을 불러오는 중...</div>
            <div v-else-if="roomsError" class="alert alert-danger">{{ roomsError }}</div>
            <ul v-else class="list-group list-group-flush">
              <li v-if="!rooms.length" class="list-group-item bg-transparent text-white-50">
                아직 공개 채팅방이 없습니다.
              </li>
              <li
                v-for="room in rooms"
                :key="room.id"
                class="list-group-item d-flex justify-content-between align-items-center bg-transparent text-light"
              >
                <div>
                  <p class="mb-0 fw-semibold">{{ room.name }}</p>
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
              </li>
            </ul>
            <button class="btn btn-outline-info nav-hover mt-3 w-100" type="button" @click="loadRooms">새로 고침</button>
          </div>
        </div>

        <div class="card border-0 mb-4">
          <div class="card-body">
            <h5 class="text-light mb-3">채팅방 생성</h5>
            <form class="row g-3" autocomplete="off" @submit.prevent="handleCreateRoom">
              <div class="col-12">
                <label class="form-label text-white-50">채팅방 이름</label>
                <input v-model="createRoomForm.name" class="form-control" maxlength="50" required />
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
                <small class="text-white-50">비공개 채팅방은 목록에 표시되지 않으며 비밀번호로만 입장합니다.</small>
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
        <div class="card border-0 h-100">
          <div class="card-body d-flex flex-column gap-3 h-100">
            <div class="d-flex justify-content-between align-items-center">
              <div>
                <h5 class="text-light mb-1">{{ currentRoom ? currentRoom.name : '채팅방을 선택해 주세요' }}</h5>
                <p class="text-white-50 mb-0">
                  {{
                    currentRoom
                      ? `정원 ${currentRoom.member_count}/${currentRoom.capacity} · ${
                          currentRoom.is_private ? '비공개' : '공개'
                        }`
                      : '좌측에서 채팅방을 선택하거나 새로 만들 수 있습니다.'
                  }}
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
              <article v-for="chat in chatMessages" :key="chat.id" class="chat-message list-group-item">
                <div class="d-flex justify-content-between">
                  <span class="fw-semibold" :class="{ 'text-warning': chat.is_anonymous }">{{ chat.display_name }}</span>
                  <small>{{ formatDate(chat.created_at) }}</small>
                </div>
                <p class="mt-1">{{ chat.content }}</p>
              </article>
            </div>
            <div v-else class="alert alert-warning">채팅방을 선택하거나 새로 만들어주세요.</div>

            <div v-if="chatError" class="alert alert-danger">{{ chatError }}</div>

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
  </section>
</template>
