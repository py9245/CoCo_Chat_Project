<script setup>
const timeline = [
  {
    phase: 'Phase 0 · 인프라 부팅',
    period: '2024 Q1',
    details: [
      'EC2 Ubuntu LTS 셋업, Docker + docker-compose로 백엔드/프런트 분리 배포',
      'RDS PostgreSQL, Elasticache Redis, S3 버킷 기본 보안 설정 (암호화, VPC 엔드포인트)',
      'Let’s Encrypt → AWS ACM으로 이전하여 자동 갱신 파이프라인 구성',
    ],
  },
  {
    phase: 'Phase 1 · 기능 MVP',
    period: '2024 Q2',
    details: [
      'Django REST + Vue SPA 기본 게시판/계정/채팅 기능 완성',
      'WebSocket 실시간 채팅 구현, Redis pub/sub, JWT 인증 연동',
      'GitHub Actions CI → GitHub Pages 정적 빌드 자동 반영',
    ],
  },
  {
    phase: 'Phase 2 · 보안 & 안정화',
    period: '2024 Q3',
    details: [
      'AWS WAF + nginx rate-limit + Fail2ban으로 DDoS 및 악성 트래픽 방어',
      'PostgreSQL row-level security, 감사 로그 테이블 추가',
      'Snyk/Dependabot + Secret Scanning으로 공급망 보안 강화',
    ],
  },
  {
    phase: 'Phase 3 · 운영 자동화',
    period: '2024 Q4',
    details: [
      'Celery 워커와 OpenSearch 기반 모니터링, Slack 알림 봇 연동',
      'WebSocket 클러스터 자동 스케일링 (KEDA + HPA) PoC',
      '프로젝트 위키/ERD/아키텍처 다이어그램을 단일 Docs 라우트로 공개',
    ],
  },
]
</script>

<template>
  <section class="panel fade-card">
    <div class="mb-4">
      <p class="text-uppercase small text-info mb-2">PROJECT TIMELINE</p>
      <h1 class="h3 text-light mb-2">CoCo-Chat 발전 과정</h1>
      <p class="text-white-50 mb-0">
        EC2 초기 셋업부터 WebSocket 스케일링, 보안 강화를 거쳐 오는 과정 전체를 정리했습니다. 각 Phase는 GitHub Projects에
        동기화되어 이슈/PR 기록과 연결됩니다.
      </p>
    </div>

    <div class="timeline">
      <article v-for="item in timeline" :key="item.phase" class="timeline-item">
        <div class="timeline-marker"></div>
        <div class="timeline-body">
          <div class="d-flex justify-content-between flex-column flex-md-row gap-2">
            <h2 class="h5 text-light mb-0">{{ item.phase }}</h2>
            <span class="badge bg-info text-dark align-self-start">{{ item.period }}</span>
          </div>
          <ul class="text-white-50 ps-3 mt-2 mb-0">
            <li v-for="detail in item.details" :key="detail">{{ detail }}</li>
          </ul>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.timeline {
  position: relative;
  padding-left: 1.5rem;
  border-left: 2px solid rgba(255, 255, 255, 0.2);
}

.timeline-item {
  position: relative;
  padding-bottom: 1.5rem;
}

.timeline-marker {
  position: absolute;
  left: -0.65rem;
  top: 0.4rem;
  width: 0.9rem;
  height: 0.9rem;
  border-radius: 50%;
  background: #0dcaf0;
  box-shadow: 0 0 8px rgba(13, 202, 240, 0.6);
}

.timeline-body {
  margin-left: 0.5rem;
}
</style>
