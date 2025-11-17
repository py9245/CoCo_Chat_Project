<script setup>
const layers = [
  {
    title: '클라이언트 & Edge',
    detail:
      'Vite로 번들된 정적 파일을 GitHub Pages + Cloudflare CDN에 배포합니다. CSP/서명 쿠키가 없어도 되도록 모든 민감 API는 서버 도메인에만 존재합니다.',
    bullets: ['GitHub Pages 정적 빌드', '서비스 워커 없이 캐시 만료 제어', 'Edge 404 → SPA 라우팅'],
  },
  {
    title: 'API & WebSocket',
    detail:
      'Django REST API와 Channels(WebSocket 서버)를 Nginx 리버스 프록시 뒤에 배치했습니다. 실시간 엔드포인트는 `/ws/chatrooms/:id/`만 열어 공격면을 축소했습니다.',
    bullets: ['Gunicorn + Uvicorn workers 혼합', '토큰 인증 + Origin 검증', '메시지 페이로드 서명 검사'],
  },
  {
    title: '데이터 & 백오피스',
    detail:
      'PostgreSQL, Redis, S3를 분리 구성했습니다. Redis는 WebSocket 세션/레이트리밋에만 사용하고, 콘텐츠는 S3 versioning을 활용합니다.',
    bullets: ['PostgreSQL 정적 역할 분리', 'Redis rate limit + pub/sub', 'S3 버저닝 + 객체 암호화'],
  },
]

const flows = [
  {
    name: '소켓 연결 흐름',
    steps: [
      '프런트에서 `/ws/chatrooms/:id/?token=JWT`로 연결 → CloudFront/Cloudflare에서 TLS 종료',
      'Nginx가 Origin, rate-limit, UA, GeoIP 룰을 점검 후 Channels worker로 라우팅',
      'Channels가 Redis pub/sub로 메시지를 fan-out 하고, PostgreSQL 트랜잭션에 영구 저장',
    ],
  },
  {
    name: 'DDoS & 악성 트래픽 방어',
    steps: [
      'AWS WAF: 초당 요청 수, GeoIP, User-Agent 패턴 룰 적용',
      'Nginx: `limit_req`, `limit_conn`, `fail2ban` 연동으로 1차 차단',
      'Redis + Celery: 실시간 IP 평판 점수화, 블록리스트를 60초 단위로 재배포',
    ],
  },
]
</script>

<template>
  <section class="panel fade-card">
    <div class="mb-4">
      <p class="text-uppercase small text-info mb-2">ARCHITECTURE</p>
      <h1 class="h3 text-light mb-2">CoCo-Chat 시스템 아키텍처</h1>
      <p class="text-white-50 mb-0">
        인프라는 AWS EC2 + RDS + S3 + CloudFront 조합으로 구성되며, GitHub Actions로 빌드 후 S3/Pages에 동시에 배포합니다.
        모든 구성 요소는 Terraform 상태 파일과 ERD 다이어그램으로 문서화되어 DevSecOps 리뷰를 쉽게 합니다.
      </p>
    </div>

    <div class="row g-4">
      <article v-for="layer in layers" :key="layer.title" class="col-12 col-lg-4">
        <div class="card h-100 border-0 bg-dark text-light">
          <div class="card-body">
            <h2 class="h5 mb-2">{{ layer.title }}</h2>
            <p class="text-white-50 mb-3">{{ layer.detail }}</p>
            <ul class="small text-white-50 ps-3 mb-0">
              <li v-for="item in layer.bullets" :key="item">{{ item }}</li>
            </ul>
          </div>
        </div>
      </article>
    </div>

    <div class="mt-4">
      <h2 class="h5 text-light mb-3">핵심 플로우</h2>
      <div class="row g-3">
        <article v-for="flow in flows" :key="flow.name" class="col-12 col-lg-6">
          <div class="card border-0 bg-black text-white h-100">
            <div class="card-body">
              <h3 class="h6 text-uppercase text-info">{{ flow.name }}</h3>
              <ol class="ps-3 small text-white-50 mb-0">
                <li v-for="step in flow.steps" :key="step">{{ step }}</li>
              </ol>
            </div>
          </div>
        </article>
      </div>
    </div>
  </section>
</template>
