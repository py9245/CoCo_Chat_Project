<script setup>
const tables = [
  {
    name: 'users',
    description: '기본 인증 정보를 저장하며 Django auth_user 테이블과 동기화됩니다.',
    fields: [
      'id (PK)',
      'username · email · password_hash',
      'is_staff · is_active · last_login',
    ],
  },
  {
    name: 'profiles',
    description: '유저 프로필 확장 영역으로 상태 메시지, 국가, 알림 설정을 포함합니다.',
    fields: ['user_id (FK → users.id)', 'status_message', 'country_code', 'notification_flags JSONB'],
  },
  {
    name: 'chat_rooms',
    description: '실시간 채팅방 정의. WebSocket 라우팅과 rate-limit 정책이 이 테이블을 참조합니다.',
    fields: ['id (PK)', 'name', 'capacity', 'is_private', 'password_hash', 'created_at'],
  },
  {
    name: 'chat_members',
    description: '실시간 참여자 목록. 익명 토큰과 실제 유저를 분리 보관해 개인정보를 보호합니다.',
    fields: ['id (PK)', 'room_id (FK → chat_rooms.id)', 'user_id (nullable FK)', 'anonymous_name', 'joined_at'],
  },
  {
    name: 'chat_messages',
    description: 'WebSocket 메시지가 영구 저장되는 테이블. soft delete와 감사 로그 컬럼을 가집니다.',
    fields: ['id (PK)', 'room_id (FK → chat_rooms.id)', 'author_id (FK)', 'is_anonymous', 'payload JSONB', 'created_at'],
  },
  {
    name: 'posts',
    description: '게시판 본문 및 메타 데이터를 포함합니다. ERD 상에서 chat_messages와 동일한 감사 전략을 공유합니다.',
    fields: ['id (PK)', 'author_id (FK → users.id)', 'title', 'body', 'status', 'created_at', 'updated_at'],
  },
]

const relationships = [
  'users 1:N profiles (1:1 관계지만 확장성을 위해 독립 테이블 구성)',
  'users 1:N chat_rooms (관리자 소유), chat_members (참여자), chat_messages (작성자)',
  'chat_rooms 1:N chat_members & chat_messages',
  'chat_members 1:N chat_messages (익명 필드 매칭)',
  'posts ↔ users, posts ↔ chat_rooms (게시글 공유 시 교차 참조)',
]
</script>

<template>
  <section class="panel fade-card">
    <div class="mb-4">
      <p class="text-uppercase small text-info mb-2">ERD DOCUMENT</p>
      <h1 class="h3 text-light mb-2">CoCo-Chat ERD 다이어그램</h1>
      <p class="text-white-50 mb-0">
        PostgreSQL 기반 정규화 모델로 구성된 데이터 구조입니다. ERD 툴에는 dbdiagram.io 스냅샷과 Prisma schema를 함께
        기록해, 코드/문서/실제 DB 간 스키마 드리프트를 자동 감지합니다.
      </p>
    </div>

    <div class="row g-4">
      <article v-for="table in tables" :key="table.name" class="col-12 col-md-6">
        <div class="card h-100 border-0 bg-dark text-light">
          <div class="card-body">
            <h2 class="h5 mb-2">{{ table.name }}</h2>
            <p class="text-white-50 mb-3">{{ table.description }}</p>
            <ul class="small text-white-50 ps-3 mb-0">
              <li v-for="field in table.fields" :key="field">{{ field }}</li>
            </ul>
          </div>
        </div>
      </article>
    </div>

    <div class="mt-4">
      <h2 class="h5 text-light mb-2">핵심 관계</h2>
      <ul class="text-white-50 ps-3">
        <li v-for="rel in relationships" :key="rel">{{ rel }}</li>
      </ul>
      <p class="text-white-50 small mb-0">
        실제 다이어그램은 GitHub Wiki와 dbdiagram 공유 링크에 동시에 게시되어, 리뷰어가 버전별 차이를 추적할 수 있습니다.
      </p>
    </div>
  </section>
</template>
