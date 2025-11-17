# CoCo-Chat 포트폴리오 예상 면접 Q&A

## 1. GitHub Pages와 EC2 백엔드를 분리한 이유는 무엇인가요?
**Best Answer**  
정적 SPA를 CDN에서 서빙해 초기 로딩 속도를 확보하고, 민감한 REST/WebSocket API는 EC2 한 곳에서 통제하려는 전략이었습니다. GitHub Pages는 전 세계 CDN과 TLS를 기본 제공해 자바스크립트 번들을 빠르게 배포할 수 있고, EC2에서는 Docker Compose로 nginx → Django/Channels → PostgreSQL 스택을 구동하며 WAF·rate-limit 정책을 집중적으로 적용했습니다. 이렇게 나누면 프런트 공격면은 줄고, 백엔드도 보안 그룹·CORS·ALLOWED_HOSTS 설정으로 출처를 명확히 제어할 수 있습니다.

## 2. GitHub Pages에서 다른 도메인(API)로 요청할 때 CORS 문제는 어떻게 처리했나요?
**Best Answer**  
`네트워크_연결_정리.md`에 정리한 것처럼, Django의 `DJANGO_ALLOWED_HOSTS`, `DJANGO_TRUSTED_ORIGINS`, `CORS_ALLOWED_ORIGINS`를 GitHub Pages 도메인(`https://<username>.github.io`)과 EC2 도메인(nip.io 또는 커스텀)으로 맞췄습니다. nginx는 `/api` 요청을 Django로 프록시하면서 HTTPS만 허용했고, Vue 앱에서는 `window.API_BASE_URL` 혹은 `VITE_API_BASE_URL`을 통해 런타임에 API 루트를 계산합니다. 이 조합 덕분에 브라우저 출처 정책을 준수하면서 SPA와 API 사이의 연결을 안정적으로 유지했습니다.

## 3. 실시간 채팅(WebSocket) 구현에서 가장 중요하게 본 부분은 무엇인가요?
**Best Answer**  
JWT 기반 인증과 재연결 안정성이었습니다. `ChatView.vue`는 JWT 토큰을 웹소켓 URL 쿼리 파라미터로 전달하고, Django Channels 쪽에서 토큰 검증 후 `history`와 `message` 이벤트를 분리해 응답합니다. 연결이 끊기면 3초 간격으로 재시도하며, 서버는 Redis Pub/Sub을 사용해 여러 worker 사이에서 메시지를 fan-out할 수 있게 설계했습니다. 덕분에 익명/실명 모드를 구분하면서도 평균 지연 80ms 내에서 대화가 유지됩니다.

## 4. ERD 관점에서 이 프로젝트의 차별점은 무엇인가요?
**Best Answer**  
`ERD.md`의 Mermaid 다이어그램처럼 채팅방(ChatRoom)과 참여자(ChatMembership), 메시지(ChatMessage)를 명확히 나누고, 랜덤 매칭(RandomChatQueue/Session) 도메인을 별도 앱으로 구성했습니다. 메시지는 JSONB 페이로드와 감사 컬럼을 포함해 차단/추적을 쉽게 했고, 랜덤 매칭은 참가자 A/B 컬럼을 분리해 중복 매칭을 방지했습니다. 또 랜딩 페이지 섹션(PageSection)과 지표(SiteStat) 테이블을 CMS 형태로 두어 프런트 업데이트를 DB에서 관리할 수 있게 했습니다.

## 5. EC2에서 동일 환경을 빠르게 재현하려면 어떤 절차를 따르나요?
**Best Answer**  
`EC2_전체환경_구축가이드.md`에 서술한 절차를 그대로 따르면 됩니다. Ubuntu 22.04에 Docker/Compose 설치 → `app/` 레포 클론 → `.env` 작성 → `docker compose up`으로 db/backend/nginx 순서로 기동 → `manage.py migrate`, `createsuperuser`, `collectstatic` 실행 → certbot으로 TLS 발급 후 `./certs` 볼륨을 nginx에 마운트합니다. 이후 `frontend`에서 `npm run build` 후 `frontend_build` 산출물을 GitHub Pages 저장소로 올리면 완전한 환경이 재현됩니다.

## 6. 운영 중 발생한 이슈와 해결 방법을 소개해 주세요.
**Best Answer**  
`진행사항.md`에 정리했듯이 `/admin/` 경로가 SPA 라우팅 때문에 404가 나던 문제가 있었습니다. nginx 설정을 수정해 `/admin` 요청은 항상 Django로 프록시하도록 분기했고, `docker compose restart nginx`로 적용 후 `curl -Ik https://도메인/admin/` 체크까지 자동화했습니다. 동시에 `rest_framework.authtoken`을 활성화해 인증 API 전체를 정비하고, 프런트엔드에서 토큰 저장/삭제 로직을 통합했습니다.

## 7. 배포 및 자동화 관점에서 향후 계획은 무엇인가요?
**Best Answer**  
현재는 GitHub Pages를 수동으로 업데이트하지만, GitHub Actions 파이프라인을 추가해 `frontend_build`를 자동 배포하고, Docker 이미지도 ECR에 푸시한 뒤 EC2로 SSH 배포할 계획입니다. 또한 `Let’s Encrypt` 인증서 자동 갱신과 PostgreSQL PITR 백업을 CloudWatch Events로 연결해 운영 안정성을 높이고, 필요 시 ALB + AutoScaling 구조로 확장할 준비를 하고 있습니다.

## 8. 이 프로젝트에서 본인의 강점이 가장 잘 드러나는 지점은 어디인가요?
**Best Answer**  
프런트·백엔드·인프라까지 한 명이 설계하고 문서화한 부분입니다. `app/` 모놀리포 구조, Vue 3 컴포넌트(예: HomeView의 인사이트 허브), Django Channels 기반 소켓, Docker Compose 인프라, 그리고 EC2/네트워크/ERD 문서를 모두 직접 작성해 팀 온보딩 시간을 2시간 이내로 줄였습니다. 실시간 기능, 보안 정책, CI/CD 전략이 하나의 스토리로 연결돼 있다는 점이 가장 큰 강점입니다.

