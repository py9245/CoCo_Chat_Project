<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import {
  fetchHealth,
  fetchHomeOverview,
  fetchRandomChatMessages,
  fetchRandomChatState,
  joinRandomChatQueue,
  leaveRandomChatQueue,
  postRandomChatMessage,
  requestRandomChatMatch,
} from '@/services/api'
import { useSession } from '@/composables/useSession'

const health = ref({ ok: null, text: 'API 상태 확인 중...' })
const sections = ref([])
const stats = ref([])
const totals = ref({ users: 0, posts: 0, messages: 0 })
const isLoading = ref(true)
const errorMessage = ref('')

const { profile, ensureProfileLoaded } = useSession()

const randomState = ref({
  in_queue: false,
  queue_position: null,
  queue_size: 0,
  session: null,
  messages: [],
})
const randomActiveTab = ref('idle')
const randomError = ref('')
const isRandomLoading = ref(false)
const isJoiningQueue = ref(false)
const isMatching = ref(false)
const isSendingRandom = ref(false)
const randomMessage = ref('')
const PHONE_BLOCK_PATTERN = /010-\d{4}-\d{4}/
const RANDOM_POLL_INTERVAL = 2000
let randomPollTimer = null

const assignRandomState = (payload = {}) => {
  randomState.value = {
    in_queue: Boolean(payload?.in_queue),
    queue_position: payload?.queue_position ?? null,
    queue_size: payload?.queue_size ?? 0,
    session: payload?.session || null,
    messages: Array.isArray(payload?.messages) ? payload.messages : [],
  }
}

const loadData = async () => {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const [healthPayload, homePayload] = await Promise.all([fetchHealth(), fetchHomeOverview()])
    health.value = {
      ok: Boolean(healthPayload?.ok),
      text: healthPayload?.ok ? 'API 정상 동작 중' : 'API 응답 이상',
    }
    sections.value = Array.isArray(homePayload?.sections) ? homePayload.sections : []
    stats.value = Array.isArray(homePayload?.stats) ? homePayload.stats : []
    totals.value = homePayload?.totals ?? { users: 0, posts: 0, messages: 0 }
  } catch (error) {
    console.error(error)
    errorMessage.value = '메인 데이터를 불러오지 못했습니다.'
  } finally {
    isLoading.value = false
  }
}

const requireRandomAuth = () => {
  if (!profile.value) {
    randomError.value = '랜덤 채팅은 로그인 후 이용할 수 있습니다.'
    return false
  }
  randomError.value = ''
  return true
}

const loadRandomState = async () => {
  if (!profile.value) return
  isRandomLoading.value = true
  randomError.value = ''
  try {
    const payload = await fetchRandomChatState({ limit: 60 })
    assignRandomState(payload)
  } catch (error) {
    console.error(error)
    randomError.value = error?.payload?.detail || '랜덤 채팅 상태를 불러오지 못했습니다.'
  } finally {
    isRandomLoading.value = false
  }
}

const handleSelectRandomTab = async (tab) => {
  randomActiveTab.value = tab
  if (tab === 'queue') {
    await handleJoinRandomQueue()
  } else if (tab === 'match') {
    await handleRequestRandomMatch()
  }
}

const handleJoinRandomQueue = async () => {
  if (!requireRandomAuth()) return
  if (isJoiningQueue.value) return
  isJoiningQueue.value = true
  randomError.value = ''
  try {
    const payload = await joinRandomChatQueue()
    assignRandomState(payload)
  } catch (error) {
    console.error(error)
    randomError.value = error?.payload?.detail || '대기열에 들어가지 못했습니다.'
  } finally {
    isJoiningQueue.value = false
  }
}

const handleLeaveRandomQueue = async () => {
  if (!profile.value) return
  randomError.value = ''
  try {
    await leaveRandomChatQueue()
    await loadRandomState()
  } catch (error) {
    console.error(error)
    randomError.value = error?.payload?.detail || '대기열에서 나갈 수 없습니다.'
  }
}

const handleRequestRandomMatch = async () => {
  if (!requireRandomAuth()) return
  if (isMatching.value) return
  isMatching.value = true
  randomError.value = ''
  try {
    const payload = await requestRandomChatMatch()
    assignRandomState(payload)
    randomMessage.value = ''
  } catch (error) {
    console.error(error)
    randomError.value =
      error?.payload?.detail ||
      (error.status === 401 ? '랜덤 채팅은 로그인 후 이용 가능합니다.' : '랜덤 매칭에 실패했습니다.')
  } finally {
    isMatching.value = false
  }
}

const refreshRandomMessages = async () => {
  if (!profile.value || !randomState.value.session) return
  try {
    const payload = await fetchRandomChatMessages({ limit: 60 })
    if (Array.isArray(payload?.messages)) {
      randomState.value = { ...randomState.value, messages: payload.messages }
    }
  } catch (error) {
    console.error(error)
  }
}

const handleSendRandomMessage = async () => {
  if (!profile.value || !randomState.value.session) {
    randomError.value = '매칭 후 메시지를 보낼 수 있습니다.'
    return
  }
  const content = randomMessage.value.trim()
  if (!content) {
    randomError.value = '메시지를 입력해 주세요.'
    return
  }
  if (PHONE_BLOCK_PATTERN.test(content)) {
    randomError.value = '전화번호 형식(010-0000-0000)은 전송할 수 없습니다.'
    return
  }
  if (isSendingRandom.value) return
  isSendingRandom.value = true
  randomError.value = ''
  try {
    const payload = await postRandomChatMessage({ content })
    randomState.value = {
      ...randomState.value,
      messages: [...randomState.value.messages, payload],
    }
    randomMessage.value = ''
  } catch (error) {
    console.error(error)
    randomError.value = error?.payload?.detail || '메시지를 보내지 못했습니다.'
  } finally {
    isSendingRandom.value = false
  }
}

const startRandomPolling = () => {
  stopRandomPolling()
  if (!randomState.value.session) return
  randomPollTimer = window.setInterval(() => {
    refreshRandomMessages()
  }, RANDOM_POLL_INTERVAL)
}

const stopRandomPolling = () => {
  if (randomPollTimer) {
    clearInterval(randomPollTimer)
    randomPollTimer = null
  }
}

watch(
  () => randomState.value.session?.id,
  (current, previous) => {
    if (current !== previous) {
      startRandomPolling()
    }
    if (!current) {
      stopRandomPolling()
    }
  },
)

watch(
  () => profile.value,
  (current) => {
    if (current) {
      loadRandomState()
    } else {
      stopRandomPolling()
      assignRandomState({})
      randomMessage.value = ''
    }
  },
  { immediate: true },
)

onMounted(async () => {
  await ensureProfileLoaded()
  loadData()
})

onUnmounted(() => {
  stopRandomPolling()
})
</script>

<template>
  <section class="panel mb-4 animate-[float_8s_ease-in-out_infinite]">
    <div class="d-flex flex-column flex-lg-row justify-content-between gap-4">
      <div>
        <div class="d-inline-flex align-items-center gap-2 mb-3 text-uppercase small fw-semibold">
          <span class="badge" :class="health.ok ? 'bg-success' : 'bg-danger'"></span>
          <span>{{ health.text }}</span>
        </div>
        <h1 class="display-5 fw-semibold text-light mb-3">Board · Account · Chat</h1>
        <p class="text-white-50 mb-4">
          Docker · Django · Postgres · Vue 스택을 한 화면에서 모니터링하고 제어할 수 있습니다.
        </p>
        <div class="d-flex flex-wrap gap-3">
          <router-link class="btn btn-primary btn-lg shadow nav-hover" to="/boards">게시판 보기</router-link>
          <router-link class="btn btn-outline-light btn-lg nav-hover" to="/chat">채팅방 열기</router-link>
        </div>
      </div>
      <div class="mini-stats row row-cols-1 g-3">
        <div class="col">
          <div class="card border-0 h-100 text-center py-3">
            <p class="text-white-50 mb-1">총 게시글</p>
            <h2 class="text-light mb-0">{{ totals.posts }}</h2>
          </div>
        </div>
        <div class="col">
          <div class="card border-0 h-100 text-center py-3">
            <p class="text-white-50 mb-1">채팅 메시지</p>
            <h2 class="text-light mb-0">{{ totals.messages }}</h2>
          </div>
        </div>
        <div class="col">
          <div class="card border-0 h-100 text-center py-3">
            <p class="text-white-50 mb-1">계정 수</p>
            <h2 class="text-light mb-0">{{ totals.users }}</h2>
          </div>
        </div>
      </div>
    </div>
  </section>

  <section class="panel random-chat-panel mb-4">
    <div class="random-chat-header">
      <div>
        <span class="random-chip">랜덤 채팅</span>
        <h2 class="random-title">한 번의 탭으로 익명 1:1 매칭</h2>
        <p class="random-subtitle">
          랜덤채팅 탭을 누르면 대기열에 합류하고, <strong>채팅하기</strong>를 누르면 본인을 제외한 다른 이용자와 즉시 연결됩니다.
          모든 대화는 익명으로만 진행됩니다.
        </p>
      </div>
      <div class="random-chat-tabs">
        <button
          class="random-chat-tab"
          :class="{ active: randomActiveTab === 'queue' }"
          :disabled="isJoiningQueue || isRandomLoading"
          type="button"
          @click="handleSelectRandomTab('queue')"
        >
          랜덤채팅 탭
        </button>
        <button
          class="random-chat-tab"
          :class="{ active: randomActiveTab === 'match' }"
          :disabled="isMatching || isRandomLoading"
          type="button"
          @click="handleSelectRandomTab('match')"
        >
          채팅하기
        </button>
      </div>
    </div>

    <div class="random-status-row">
      <div class="status-pill">
        <span class="label">대기열</span>
        <strong>{{ randomState.queue_size }}명</strong>
      </div>
      <div class="status-pill">
        <span class="label">내 순서</span>
        <strong>{{ randomState.queue_position ?? '-' }}</strong>
      </div>
      <div class="status-pill">
        <span class="label">현재 상태</span>
        <strong>
          {{ randomState.session ? randomState.session.partner_alias + ' 연결됨' : randomState.in_queue ? '대기 중' : '탭을 눌러 시작하세요' }}
        </strong>
      </div>
      <button
        v-if="randomState.in_queue"
        class="btn btn-outline-light nav-hover ms-auto random-leave-btn"
        type="button"
        @click="handleLeaveRandomQueue"
      >
        대기열 나가기
      </button>
    </div>

    <div v-if="randomError" class="alert alert-danger random-alert">{{ randomError }}</div>

    <div v-if="!profile" class="alert alert-warning random-alert">
      로그인한 사용자만 랜덤 채팅에 참여할 수 있습니다. 계정 탭에서 로그인해 주세요.
    </div>

    <div class="random-chat-body" :class="{ disabled: !profile }">
      <div class="random-stream" v-if="randomState.session && randomState.messages.length">
        <article
          v-for="message in randomState.messages"
          :key="message.id"
          class="random-chat-message"
          :class="{ me: message.from_self }"
        >
          <small>{{ message.from_self ? '나' : randomState.session.partner_alias }}</small>
          <p>{{ message.content }}</p>
          <time>{{ new Date(message.created_at).toLocaleTimeString('ko-KR') }}</time>
        </article>
      </div>
      <div v-else class="random-placeholder">
        {{
          randomState.session
            ? '아직 대화가 없습니다. 첫 메시지를 보내보세요!'
            : '대기열에 합류하고 채팅하기를 누르면 새로운 익명 채팅방이 열립니다.'
        }}
      </div>

      <form
        v-if="profile && randomState.session"
        class="random-chat-form"
        autocomplete="off"
        @submit.prevent="handleSendRandomMessage"
      >
        <textarea
          v-model="randomMessage"
          class="form-control"
          maxlength="500"
          placeholder="010-0000-0000 형식의 연락처는 전송이 제한됩니다."
        ></textarea>
        <button class="btn btn-light nav-hover" :disabled="isSendingRandom || !randomMessage.trim()" type="submit">
          <span v-if="isSendingRandom">전송 중...</span>
          <span v-else>메시지 전송</span>
        </button>
      </form>
    </div>
  </section>

  <section class="panel mb-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <div>
        <h2 class="h4 text-light mb-1">애플리케이션 개요</h2>
        <p class="text-white-50 mb-0">각 영역은 독립 라우트/앱으로 나뉘어 있습니다.</p>
      </div>
      <button class="btn btn-outline-info nav-hover" type="button" @click="loadData">새로 고침</button>
    </div>

    <div v-if="errorMessage" class="alert alert-danger">{{ errorMessage }}</div>
    <div v-else-if="isLoading" class="panel-placeholder">데이터를 불러오는 중...</div>

    <div v-else class="row g-4">
      <div v-for="section in sections" :key="section.id" class="col-12 col-md-6 col-xl-3">
        <div class="card h-100 border-0 fade-card">
          <div class="card-body d-flex flex-column gap-2">
            <span class="badge bg-secondary text-uppercase w-auto">{{ section.slug }}</span>
            <h5 class="card-title text-light mb-0">{{ section.title }}</h5>
            <p class="card-text text-white-50 flex-grow-1">{{ section.description }}</p>
            <router-link
              v-if="section.cta_link"
              class="btn btn-sm btn-outline-light align-self-start nav-hover"
              :to="section.cta_link"
            >
              {{ section.cta_label || '바로가기' }}
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </section>

  <section class="panel">
    <div class="mb-3">
      <h2 class="h4 text-light mb-1">운영 수치</h2>
      <p class="text-white-50 mb-0">DB, 백엔드, 프런트엔드가 공유하는 제약 조건입니다.</p>
    </div>

    <div v-if="stats.length" class="row g-3">
      <div v-for="stat in stats" :key="stat.id" class="col-12 col-md-6 col-xl-4">
        <div class="card border-0 h-100 mini-stat-card">
          <div class="card-body">
            <p class="text-white-50 mb-1">{{ stat.name }}</p>
            <h3 class="text-light mb-2">
              {{ stat.value }} <small class="text-white-50">{{ stat.unit }}</small>
            </h3>
            <p class="mb-0 text-white-50">{{ stat.description }}</p>
          </div>
        </div>
      </div>
    </div>
    <p v-else class="panel-placeholder">등록된 지표가 없습니다.</p>
  </section>
</template>
