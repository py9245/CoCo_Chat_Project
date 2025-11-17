<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchHealth, fetchHomeOverview } from '@/services/api'

const health = ref({ ok: null, text: 'API 상태 확인 중...' })
const sections = ref([])
const stats = ref([])
const totals = ref({ users: 0, posts: 0, rooms: 0 })
const isLoading = ref(true)
const errorMessage = ref('')
const projectTabs = [
  {
    id: 'erd',
    title: 'ERD & 데이터 모델',
    description:
      'PostgreSQL 기반 정규화 모델을 사용해 대화, 계정, 알림 데이터를 분리했습니다. ERD 다이어그램으로 관계형 구조를 한눈에 파악하고 변경 이력을 기록합니다.',
    features: ['PostgreSQL 보안 정책 + 역할 기반 접근 제어', 'ERD 기준 FK 제약 및 데이터 무결성 확보', '백업 및 PITR 스냅샷으로 장애 시점 복구'],
    route: { path: '/docs/erd' },
    cta: 'ERD 다이어그램 보기',
  },
  {
    id: 'architecture',
    title: '아키텍처 & 인프라',
    description:
      'WebSocket 기반 실시간 채팅과 Django REST API를 분리 배포했습니다. GitHub Pages 정적 빌드로 프런트 공격면을 줄이고, AWS WAF + nginx rate-limit으로 디도스 및 악의적인 트래픽을 방어합니다.',
    features: ['WebSocket 소켓 구현 + 재연결 로직', 'DDoS 방어용 rate-limit & 오토 블록', '정적 빌드/Edge Cache로 민감 정보 노출 차단'],
    route: { path: '/docs/architecture' },
    cta: '아키텍처 흐름 보기',
  },
  {
    id: 'roadmap',
    title: '프로젝트 발전 과정',
    description:
      '프로토타입 → MFA 로그인 → 소켓 클러스터링 → 악성 메시지 필터링까지 단계별 발전 과정을 타임라인으로 정리했습니다. 추후에는 자동화 방어룰과 지능형 분석을 추가할 예정입니다.',
    features: ['v1: REST 게시판 + 기본 채팅', 'v2: 소켓 스케일아웃 & DDoS 관제', 'v3: GitHub Actions 보안 스캔 + PostgreSQL 암호화'],
    route: { path: '/docs/roadmap' },
    cta: '발전 과정 살펴보기',
  },
]
const activeProjectTab = ref(projectTabs[0].id)
const activeTabContent = computed(() => projectTabs.find((tab) => tab.id === activeProjectTab.value) || projectTabs[0])

const loadData = async () => {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const [healthPayload, homePayload] = await Promise.all([fetchHealth(), fetchHomeOverview()])
    health.value = {
      ok: Boolean(healthPayload?.ok),
      text: healthPayload?.ok ? 'API 정상 동작 중' : 'API 응답 이상',
    }
    const fetchedSections = Array.isArray(homePayload?.sections) ? homePayload.sections : []
    const heroSection = {
      id: '__random_chat_card',
      slug: 'RANDOM_CHAT',
      title: '랜덤 채팅',
      description: '대기열에서 무작위 이용자와 바로 매칭되어 1:1 대화를 즐길 수 있습니다.',
      cta_label: '랜덤 채팅으로 이동',
      cta_link: '/random-chat.html',
    }
    sections.value = [
      heroSection,
      ...fetchedSections.filter(
        (section) => (section.slug || '').toString().toUpperCase() !== 'HERO' && section.slug !== heroSection.slug
      ),
    ]
    stats.value = Array.isArray(homePayload?.stats) ? homePayload.stats : []
    totals.value = homePayload?.totals ?? { users: 0, posts: 0, rooms: 0 }
  } catch (error) {
    console.error(error)
    errorMessage.value = '메인 데이터를 불러오지 못했습니다.'
  } finally {
    isLoading.value = false
  }
}

onMounted(loadData)

const setActiveProjectTab = (id) => {
  activeProjectTab.value = id
}
</script>

<template>
  <section class="panel mb-4 animate-[float_8s_ease-in-out_infinite]">
    <div class="d-flex flex-column flex-lg-row justify-content-between gap-4">
      <div>
        <div class="d-inline-flex align-items-center gap-2 mb-3 text-uppercase small fw-semibold">
          <span class="badge" :class="health.ok ? 'bg-success' : 'bg-danger'"></span>
          <span>{{ health.text }}</span>
        </div>
        <h1 class="display-5 fw-semibold text-light mb-3">CoCo-Chat</h1>
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
            <p class="text-white-50 mb-1">오픈 채팅방</p>
            <h2 class="text-light mb-0">{{ totals.rooms }}</h2>
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
    <div class="d-flex flex-column flex-lg-row justify-content-between gap-3 mb-4">
      <div>
        <h2 class="h4 text-light mb-2">프로젝트 인사이트 허브</h2>
        <p class="text-white-50 mb-0">
          ERD, 시스템 아키텍처, 발전 과정을 탭으로 살펴보며 소켓 구현, 디도스 방어, 악의적인 트래픽 차단, GitHub Pages 정적 빌드,
          PostgreSQL 보안 전략을 확인하세요.
        </p>
      </div>
      <div class="d-flex flex-wrap gap-2">
        <button
          v-for="tab in projectTabs"
          :key="tab.id"
          type="button"
          :class="[
            'btn',
            'nav-hover',
            activeProjectTab === tab.id ? 'btn-info text-white' : 'btn-outline-info text-light',
          ]"
          @click="setActiveProjectTab(tab.id)"
        >
          {{ tab.title }}
        </button>
      </div>
    </div>
    <div class="card border-0 fade-card">
      <div class="card-body">
        <span class="badge bg-secondary text-uppercase w-auto">{{ activeTabContent.id }}</span>
        <h3 class="h5 text-light mt-3 mb-2">{{ activeTabContent.title }}</h3>
        <p class="text-white-50 mb-3">{{ activeTabContent.description }}</p>
        <ul class="text-white-50 small ps-3 mb-4">
          <li v-for="feature in activeTabContent.features" :key="feature">{{ feature }}</li>
        </ul>
        <router-link v-if="activeTabContent.route" class="btn btn-outline-light nav-hover" :to="activeTabContent.route">
          {{ activeTabContent.cta || '자세히 보기' }}
        </router-link>
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
