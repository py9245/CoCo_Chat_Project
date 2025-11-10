<script setup>
import { onMounted, reactive, ref } from 'vue'
import { createPost, deletePost, fetchPosts, updatePost } from '@/services/api'
import { useSession } from '@/composables/useSession'

const { profile, ensureProfileLoaded } = useSession()

const posts = ref([])
const isLoading = ref(true)
const formError = ref('')
const formSuccess = ref('')
const isSubmitting = ref(false)
const postForm = reactive({ title: '', body: '', attachment: null })
const attachmentName = ref('')
const attachmentInput = ref(null)
const editingPostId = ref(null)
const editForm = reactive({ title: '', body: '', attachment: null, clearAttachment: false })
const editAttachmentName = ref('')
const editAttachmentInput = ref(null)
const isUpdatingPost = ref(false)
const deletingPostId = ref(null)

const formatDate = (value) => {
  if (!value) return ''
  const date = typeof value === 'string' ? new Date(value) : value
  if (Number.isNaN(date.getTime())) return ''
  return new Intl.DateTimeFormat('ko-KR', { dateStyle: 'long', timeStyle: 'short' }).format(date)
}

const handleAttachmentChange = (event) => {
  const [file] = event.target.files || []
  postForm.attachment = file || null
  attachmentName.value = file ? `${file.name} (${(file.size / (1024 * 1024)).toFixed(2)}MB)` : ''
}

const resetAttachmentInput = () => {
  postForm.attachment = null
  attachmentName.value = ''
  if (attachmentInput.value) {
    attachmentInput.value.value = ''
  }
}

const resetEditAttachment = () => {
  editForm.attachment = null
  editAttachmentName.value = ''
  if (editAttachmentInput.value) {
    editAttachmentInput.value.value = ''
  }
}

const loadPosts = async () => {
  isLoading.value = true
  try {
    const payload = await fetchPosts()
    posts.value = Array.isArray(payload?.posts) ? payload.posts : []
  } catch (error) {
    console.error(error)
    formError.value = '게시글을 불러오지 못했습니다.'
  } finally {
    isLoading.value = false
  }
}

const handleSubmit = async () => {
  formError.value = ''
  formSuccess.value = ''
  if (!profile.value) {
    formError.value = '로그인 후 이용해 주세요.'
    return
  }
  if (!postForm.title.trim()) {
    formError.value = '제목을 입력해 주세요.'
    return
  }
  isSubmitting.value = true
  try {
    const formData = new FormData()
    formData.append('title', postForm.title.trim())
    formData.append('body', postForm.body.trim())
    if (postForm.attachment) {
      formData.append('attachment', postForm.attachment)
    }
    const payload = await createPost(formData)
    posts.value = [payload, ...posts.value]
    postForm.title = ''
    postForm.body = ''
    resetAttachmentInput()
    formSuccess.value = '게시글이 등록되었습니다.'
  } catch (error) {
    console.error(error)
    formError.value =
      error?.payload?.detail ||
      (Array.isArray(error?.payload?.non_field_errors) ? error.payload.non_field_errors.join(' ') : '게시글을 저장하지 못했습니다.')
  } finally {
    isSubmitting.value = false
  }
}

const startEdit = (post) => {
  editingPostId.value = post.id
  editForm.title = post.title
  editForm.body = post.body || ''
  editForm.clearAttachment = false
  resetEditAttachment()
}

const cancelEdit = () => {
  editingPostId.value = null
  editForm.title = ''
  editForm.body = ''
  editForm.clearAttachment = false
  resetEditAttachment()
}

const handleEditAttachmentChange = (event) => {
  const [file] = event.target.files || []
  editForm.attachment = file || null
  editAttachmentName.value = file ? `${file.name} (${(file.size / (1024 * 1024)).toFixed(2)}MB)` : ''
  if (file) {
    editForm.clearAttachment = false
  }
}

const handleEditSubmit = async () => {
  if (!editingPostId.value) return
  formError.value = ''
  isUpdatingPost.value = true
  try {
    const formData = new FormData()
    formData.append('title', editForm.title.trim())
    formData.append('body', editForm.body.trim())
    if (editForm.attachment) {
      formData.append('attachment', editForm.attachment)
    }
    if (editForm.clearAttachment && !editForm.attachment) {
      formData.append('clear_attachment', '1')
    }
    const payload = await updatePost(editingPostId.value, formData)
    posts.value = posts.value.map((post) => (post.id === payload.post.id ? payload.post : post))
    cancelEdit()
  } catch (error) {
    console.error(error)
    formError.value = error?.payload?.detail || '게시글을 수정하지 못했습니다.'
  } finally {
    isUpdatingPost.value = false
  }
}

const handleDeletePost = async (postId) => {
  if (!window.confirm('해당 게시글을 삭제하시겠습니까?')) return
  formError.value = ''
  deletingPostId.value = postId
  try {
    await deletePost(postId)
    posts.value = posts.value.filter((post) => post.id !== postId)
    if (editingPostId.value === postId) {
      cancelEdit()
    }
  } catch (error) {
    console.error(error)
    formError.value = error?.payload?.detail || '게시글을 삭제하지 못했습니다.'
  } finally {
    deletingPostId.value = null
  }
}

onMounted(async () => {
  await Promise.all([ensureProfileLoaded(), loadPosts()])
})
</script>

<template>
  <section class="panel">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <div>
        <h2 class="h4 text-light mb-1">파일 첨부 게시판</h2>
        <p class="text-white-50 mb-0">첨부파일은 AWS S3에 저장되며 계정당 하루 5개까지 작성 가능합니다.</p>
      </div>
      <button class="btn btn-outline-info nav-hover" type="button" @click="loadPosts">새로 고침</button>
    </div>

    <div v-if="profile" class="post-form mb-4">
      <form class="row g-3" autocomplete="off" @submit.prevent="handleSubmit">
        <div class="col-12">
          <label class="form-label text-white-50">제목</label>
          <input v-model="postForm.title" class="form-control" placeholder="게시글 제목" required />
        </div>
        <div class="col-12">
          <label class="form-label text-white-50">내용</label>
          <textarea v-model="postForm.body" class="form-control" rows="4" placeholder="전하고 싶은 이야기를 적어보세요"></textarea>
        </div>
        <div class="col-12">
          <label class="form-label text-white-50">첨부파일</label>
          <div class="d-flex flex-column flex-lg-row gap-3 align-items-lg-center">
            <label class="btn btn-outline-light w-100 w-lg-auto nav-hover mb-0" for="post-attachment">
              파일 선택
            </label>
            <span class="text-white-50">{{ attachmentName || '최대 5MB, 이미지·문서 업로드 지원' }}</span>
          </div>
          <input
            id="post-attachment"
            ref="attachmentInput"
            type="file"
            class="d-none"
            accept="image/*,application/pdf,application/zip,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.txt"
            @change="handleAttachmentChange"
          />
        </div>
        <div class="col-12 d-flex gap-3 flex-wrap">
          <button class="btn btn-primary nav-hover" :disabled="isSubmitting" type="submit">
            <span v-if="isSubmitting">업로드 중...</span>
            <span v-else>게시글 등록</span>
          </button>
          <p class="text-white-50 mb-0">파일은 최대 5MB, 하루 5개의 게시글 제한이 적용됩니다.</p>
        </div>
      </form>
    </div>
    <div v-else class="alert alert-warning">로그인한 사용자만 게시글을 작성할 수 있습니다.</div>

    <p v-if="formSuccess" class="text-success fw-semibold">{{ formSuccess }}</p>
    <p v-if="formError" class="text-danger fw-semibold">{{ formError }}</p>

    <div v-if="isLoading" class="panel-placeholder">게시글을 불러오는 중...</div>
    <div v-else-if="!posts.length" class="panel-placeholder">아직 게시글이 없습니다. 첫 글을 남겨보세요!</div>
    <div v-else class="d-flex flex-column gap-3">
      <article
        v-for="post in posts"
        :key="post.id"
        class="post-card"
        :class="{ editing: editingPostId === post.id }"
      >
        <div class="d-flex justify-content-between gap-3 flex-wrap">
          <div>
            <h5 class="mb-1 text-light">{{ post.title }}</h5>
            <small class="text-white-50">@{{ post.author?.username || '알 수 없음' }}</small>
          </div>
          <time class="text-white-50">{{ formatDate(post.created_at) }}</time>
        </div>
        <p v-if="post.body" class="text-white-50 mt-2 mb-0">{{ post.body }}</p>
        <a
          v-if="post.attachment_url"
          :href="post.attachment_url"
          class="btn btn-sm btn-outline-light mt-3 nav-hover"
          target="_blank"
          rel="noreferrer"
        >
          첨부파일 다운로드
        </a>
        <div v-if="profile?.user?.id === post.author?.id" class="d-flex gap-2 flex-wrap mt-3">
          <button class="btn btn-outline-info btn-sm nav-hover" type="button" @click="startEdit(post)">수정</button>
          <button
            class="btn btn-outline-danger btn-sm nav-hover"
            type="button"
            :disabled="deletingPostId === post.id"
            @click="handleDeletePost(post.id)"
          >
            <span v-if="deletingPostId === post.id">삭제 중...</span>
            <span v-else>삭제</span>
          </button>
        </div>

        <form
          v-if="editingPostId === post.id"
          class="mt-3 border-top pt-3"
          autocomplete="off"
          @submit.prevent="handleEditSubmit"
        >
          <div class="mb-3">
            <label class="form-label text-white-50">제목</label>
            <input v-model="editForm.title" class="form-control" required />
          </div>
          <div class="mb-3">
            <label class="form-label text-white-50">내용</label>
            <textarea v-model="editForm.body" class="form-control" rows="3"></textarea>
          </div>
          <div class="mb-3">
            <label class="form-label text-white-50">새 첨부파일</label>
            <div class="d-flex flex-column flex-lg-row gap-3 align-items-lg-center">
              <label
                class="btn btn-outline-light w-100 w-lg-auto nav-hover mb-0"
                :for="`edit-attachment-${post.id}`"
              >
                파일 선택
              </label>
              <span class="text-white-50">{{ editAttachmentName || '선택하지 않으면 기존 파일 유지' }}</span>
            </div>
            <input
              :id="`edit-attachment-${post.id}`"
              ref="editAttachmentInput"
              type="file"
              class="d-none"
              accept="image/*,application/pdf,application/zip,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.txt"
              @change="handleEditAttachmentChange"
            />
          </div>
          <div class="form-check form-switch mb-3">
            <input
              :id="`clear-attachment-${post.id}`"
              v-model="editForm.clearAttachment"
              class="form-check-input"
              type="checkbox"
              :disabled="Boolean(editForm.attachment)"
            />
            <label class="form-check-label text-white-50" :for="`clear-attachment-${post.id}`">기존 첨부 삭제</label>
          </div>
          <div class="d-flex gap-3 flex-wrap">
            <button class="btn btn-primary nav-hover" :disabled="isUpdatingPost" type="submit">
              <span v-if="isUpdatingPost">저장 중...</span>
              <span v-else>수정 완료</span>
            </button>
            <button class="btn btn-outline-light nav-hover" type="button" @click="cancelEdit">수정 취소</button>
          </div>
        </form>
      </article>
    </div>
  </section>
</template>
