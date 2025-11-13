# 프런트엔드 · 백엔드 데이터 교환 명세 (다중 앱 구조)

Vue Router 기반 SPA(`frontend/src/router/index.js`)는 `frontend/src/services/api.js`의 fetch 유틸을 통해 Django REST 다중 앱(`accounts`, `boards`, `chatrooms`, `pages`)과 통신한다. 아래 명세는 공통 규칙과 페이지별 API 계약을 설명한다.

## 1. 공통 규칙
- **기본 URL**: `API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? window.API_BASE_URL ?? (호스트가 github.io라면 https://15-164-232-40.nip.io/api, 그 외에는 `${origin}/api`).`
- **헤더**: 모든 요청 `Accept: application/json`. JSON Body가 있을 때 `Content-Type: application/json`. 인증 후에는 `Authorization: Token <DRF 토큰>`.
- **토큰 저장**: `saveAuthToken()`이 LocalStorage에 저장, `useSession()` 컴포저블이 애플리케이션 전역에서 공유.
- **시간**: 서버는 ISO8601 문자열을 반환하고 프런트는 `Intl.DateTimeFormat('ko-KR')`으로 포맷.
- **파일 업로드**: 게시글 첨부·아바타는 `multipart/form-data`로 전달하며, `requestMultipart()`가 자동으로 인증 헤더만 붙인다(콘텐츠 타입은 브라우저가 결정).

## 2. 엔드포인트 요약

| 영역 | HTTP | 경로 (prefix `/api`) | 인증 | 요청 | 응답 |
| --- | --- | --- | --- | --- | --- |
| **Pages** | GET | `/healthz` | 불필요 | - | `{ "ok": bool }` |
|  | GET | `/pages/home` | 불필요 | - | `{ "sections": [...], "stats": [...], "totals": { users, posts, messages } }` |
| **Accounts** | POST | `/accounts/register` | 불필요 | `{ username, email, password, name }` (`name`: 한글 2~5자) | `{ token, profile }` |
|  | POST | `/accounts/login` | 불필요 | `{ username, password }` | `{ token, profile }` |
|  | POST | `/accounts/logout` | 필요 | - | `{ detail }` |
|  | GET | `/accounts/profile` | 필요 | - | `{ profile }` |
|  | PATCH | `/accounts/profile/update` | 필요 | `{ display_name?, bio? }` | `{ profile }` |
|  | POST | `/accounts/profile/password` | 필요 | `{ current_password, new_password }` | `{ detail, token }` |
|  | POST | `/accounts/profile/avatar` | 필요 | `multipart/form-data(avatar)` | `{ profile }` |
|  | POST | `/accounts/profile/delete` | 필요 | `{ password }` | `{ detail }` (계정 삭제 후 토큰 무효) |
| **Boards** | GET | `/boards/posts` | 불필요 | - | `{ posts: [ { id, title, body, attachment_url, created_at, author } ] }` |
|  | POST | `/boards/posts` | 필요 | `multipart/form-data(title, body, attachment?)` | `{ id, title, body, attachment_url, created_at, author }` |
|  | PATCH | `/boards/posts/<id>` | 필요 | `multipart/form-data(title?, body?, attachment?, clear_attachment?)` | `{ post: {...} }` |
|  | DELETE | `/boards/posts/<id>` | 필요 | - | `204 No Content` |
| **Chatrooms - Rooms** | GET | `/chat/messages?limit=1..150` | 선택 | - | `{ messages: [ { id, content, created_at, is_anonymous, display_name } ] }` |
|  | POST | `/chat/messages` | 필요 | `{ content, is_anonymous }` | `{ ...same as 위 }` |
| **Chatrooms - Random** | GET | `/chat/random/state?limit=1..80` | 필요 | - | `{ in_queue, queue_position, queue_size, session, messages }` |
|  | POST | `/chat/random/queue` | 필요 | - | `state payload` |
|  | DELETE | `/chat/random/queue` | 필요 | - | `{ detail }` |
|  | POST | `/chat/random/match` | 필요 | - | `state payload (새 세션 포함)` |
|  | GET | `/chat/random/messages?limit=1..80` | 필요 | - | `{ messages: [ { id, content, created_at, from_self } ] }` |
|  | POST | `/chat/random/messages` | 필요 | `{ content }` | `{ id, content, created_at, from_self }` |

## 3. 페이지별 흐름
### 3.1 HomeView (`/`)
1. 마운트 시 `fetchHealth()`와 `fetchHomeOverview()`를 동시에 실행.
2. 응답 데이터로 상태 점등, 섹션 카드, 통계 카드, 누적 수치를 표시.
3. 새로고침 버튼은 동일한 Promise.all을 재사용.

### 3.2 BoardsView (`/boards`)
1. 최초 진입 시 `ensureProfileLoaded()`와 `fetchPosts()` 병렬 실행.
2. 글 작성 시 `FormData`로 제목·본문·첨부를 보내고 성공 응답을 리스트 앞에 추가.
3. 서버 제약: 계정당 하루 5개(`Post.objects.for_today(user)`), 첨부 5MB, 업로드 경로 `boards/{userPk-username}/userPk-username-uuid.ext` (S3 저장).

### 3.3 ChatView (`/chat`)
1. 컴포넌트 마운트 → `ensureProfileLoaded()` → `fetchChatMessages(limit=80)` → 0.5초 간격 `setInterval`.
2. 메시지 전송 시 `postChatMessage()` 호출, 응답을 현지 배열 끝에 붙이고 슬라이싱으로 80개 유지.
3. 독립 HTML(`frontend/public/chat.html`)도 동일 API를 사용하며 별도 토큰 없이 읽기 가능, 0.5초 폴링.

### 3.4 Home Random Chat
1. 홈 중앙 패널에서 `fetchRandomChatState(limit=60)`으로 대기열, 세션, 메시지를 한 번에 불러온다.
2. **랜덤채팅 탭** 버튼은 `joinRandomChatQueue()`를 호출해 대기열에 합류하고, **채팅하기** 버튼은 `requestRandomChatMatch()`로 본인을 제외한 다른 이용자와 1:1 세션을 생성한다.
3. 매칭 후 메시지는 `fetchRandomChatMessages()`를 2초 간격으로 폴링하고, 전송은 `postRandomChatMessage({ content })`로 처리한다.
4. 모든 랜덤 채팅은 익명이며, 서버/클라이언트 모두 `010-0000-0000` 형식이 포함된 메시지를 거부한다.

### 3.5 AccountsView (`/accounts`)
1. 비로그인 상태: 회원가입/로그인 폼이 `registerUser()`, `loginUser()` 호출.
2. 로그인 후: 프로필 카드 + 수정 폼 + 아바타 업로드 + 비밀번호 변경 폼이 각각 `updateProfile()`, `uploadAvatar()`, `changePassword()`를 호출.
3. 비밀번호 변경 시 DRF 토큰이 재발급되므로, 응답 `token`을 받아 `setSession(token, profile)`로 교체.

## 4. 백엔드 제약 및 설계 근거
- 앱 분리: `accounts`, `boards`, `chatrooms`, `pages`가 각각 모델/시리얼라이저/URL을 보유. `INSTALLED_APPS`에서 `core`를 제거해 역할을 분리.
- 파일 네이밍: 모든 업로드 경로는 `사용자PK-아이디` Prefix + UUID Suffix → S3에서 충돌 없이 사용자별 버킷 폴더를 확인할 수 있음.
- 일일 게시글 제한: Serializer에서 `Post.objects.for_today(user).count()` 체크로 API, DB 모두 동일 규칙을 공유.
- 채팅 폴링: 서버는 단순 REST 응답만 제공하고, 프런트가 500ms 간격으로 `GET /chat/messages`를 호출해 실시간 UX를 제공.
- 홈 대시보드: `pages.PageSection`, `pages.SiteStat` 모델로 구성되어 운영자가 Django Admin에서 콘텐츠를 관리할 수 있도록 설계.

## 5. 오류 포맷 & 처리
- `ValidationError`: `{ "field": ["메시지"] }` → 프런트는 `Object.values().flat()`으로 병합 후 한글 문장 노출.
- `detail` 키: 인증 실패, 권한 문제, 일일 제한 초과 등 주요 제약을 한글 문장으로 내려 클라이언트가 그대로 보여준다.
- 파일 제한 초과: `PostSerializer.validate_attachment()`가 5MB 초과 시 `첨부파일은 최대 5MB...` 메시지 반환.
- 로그인 필요: 인증되지 않은 상태에서 보호된 엔드포인트 접근 시 DRF가 401/403 + `{ detail: "로그인이 필요합니다." }` 반환.

## 6. 연동 체크리스트
1. `.env`에 `USE_S3=1` + `AWS_*` 자격 증명이 있어야 첨부/아바타 URL이 정상적으로 서빙된다.
2. `docker compose exec backend python manage.py migrate`로 신규 앱(`accounts`, `boards`, `chatrooms`, `pages`) 마이그레이션을 반드시 반영.
3. 프런트 빌드 후 `frontend_build/`를 nginx 정적 루트로 복사해야 라우팅이 동작한다(nginx는 history fallback 설정).
4. 독립 채팅 페이지를 포함해 모든 클라이언트는 동일 토큰 키(`codex_auth_token`)를 공유하므로, 로컬스토리지 정리가 필요할 때는 `clearAuthToken()`을 호출한다.
