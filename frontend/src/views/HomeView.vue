<script setup>
import { onMounted, ref } from 'vue'
import { fetchHealth, fetchHomeOverview } from '@/services/api'

const health = ref({ ok: null, text: 'API 상태 확인 중...' })
const sections = ref([])
const stats = ref([])
const totals = ref({ users: 0, posts: 0, messages: 0 })
const isLoading = ref(true)
const errorMessage = ref('')

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

onMounted(loadData)
</script>

<template>
  <section class="panel mb-4 animate-[float_8s_ease-in-out_infinite]">
    <div class="d-flex flex-column flex-lg-row justify-content-between gap-4">
      <div>
        <div class="d-inline-flex align-items-center gap-2 mb-3 text-uppercase small fw-semibold">
          <span class="badge" :class="health.ok ? 'bg-success' : 'bg-danger'"></span>
          <span>{{ health.text }}</span>
        </div>
        <h1 class="display-5 fw-semibold text-light mb-3">Codex Platform</h1>
        <p class="text-white-50 mb-4">게시판 · 계정 · 채팅을 한 곳에서 관리하고, 익명 랜덤 채팅은 전용 화면에서 즐겨보세요.</p>
        <div class="d-flex flex-wrap gap-3">
          <a class="btn btn-primary btn-lg shadow nav-hover" href="/random-chat.html">랜덤 채팅 열기</a>
          <router-link class="btn btn-outline-light btn-lg nav-hover" to="/chat">공개 채팅방 보기</router-link>
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
