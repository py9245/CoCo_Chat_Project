<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import {
  changePassword,
  deleteAccount,
  loginUser,
  logoutUser,
  registerUser,
  updateProfile,
  uploadAvatar,
} from '@/services/api'
import { useSession } from '@/composables/useSession'

const { profile, setSession, clearSession, ensureProfileLoaded } = useSession()

const registerForm = reactive({ username: '', email: '', password: '', name: '' })
const loginForm = reactive({ username: '', password: '' })
const profileForm = reactive({ display_name: '', bio: '' })
const passwordForm = reactive({ current_password: '', new_password: '' })
const avatarFile = ref(null)
const deleteForm = reactive({ password: '' })

const feedback = reactive({
  success: '',
  error: '',
})

const isRegistering = ref(false)
const isLoggingIn = ref(false)
const isUpdatingProfile = ref(false)
const isChangingPassword = ref(false)
const isUploadingAvatar = ref(false)
const isDeletingAccount = ref(false)

const avatarPreview = computed(() => profile.value?.avatar_url || '')

const resetFeedback = () => {
  feedback.success = ''
  feedback.error = ''
}

const syncProfileForm = () => {
  profileForm.display_name = profile.value?.display_name || ''
  profileForm.bio = profile.value?.bio || ''
}

const handleRegister = async () => {
  resetFeedback()
  isRegistering.value = true
  try {
    const payload = await registerUser({
      username: registerForm.username.trim(),
      email: registerForm.email.trim(),
      password: registerForm.password,
      name: registerForm.name.trim(),
    })
    setSession(payload.token, payload.profile)
    syncProfileForm()
    registerForm.username = ''
    registerForm.email = ''
    registerForm.password = ''
    registerForm.name = ''
    feedback.success = '회원가입이 완료되었습니다.'
  } catch (error) {
    feedback.error = error?.payload?.detail || '회원가입에 실패했습니다.'
  } finally {
    isRegistering.value = false
  }
}

const handleLogin = async () => {
  resetFeedback()
  isLoggingIn.value = true
  try {
    const payload = await loginUser({
      username: loginForm.username.trim(),
      password: loginForm.password,
    })
    setSession(payload.token, payload.profile)
    syncProfileForm()
    loginForm.username = ''
    loginForm.password = ''
    feedback.success = '로그인이 완료되었습니다.'
  } catch (error) {
    feedback.error = error?.payload?.detail || '로그인에 실패했습니다.'
  } finally {
    isLoggingIn.value = false
  }
}

const handleLogout = async () => {
  resetFeedback()
  try {
    await logoutUser()
  } catch (error) {
    console.warn('로그아웃 요청 실패', error)
  } finally {
    clearSession()
    feedback.success = '로그아웃되었습니다.'
  }
}

const handleProfileUpdate = async () => {
  resetFeedback()
  isUpdatingProfile.value = true
  try {
    const payload = await updateProfile({
      display_name: profileForm.display_name,
      bio: profileForm.bio,
    })
    setSession(undefined, payload.profile)
    feedback.success = '프로필을 업데이트했습니다.'
  } catch (error) {
    feedback.error = error?.payload?.detail || '프로필을 수정하지 못했습니다.'
  } finally {
    isUpdatingProfile.value = false
  }
}

const handleAvatarChange = (event) => {
  const [file] = event.target.files || []
  avatarFile.value = file || null
}

const handleAvatarUpload = async () => {
  if (!avatarFile.value) return
  resetFeedback()
  isUploadingAvatar.value = true
  try {
    const formData = new FormData()
    formData.append('avatar', avatarFile.value)
    const payload = await uploadAvatar(formData)
    setSession(undefined, payload.profile)
    avatarFile.value = null
    feedback.success = '아바타를 업데이트했습니다.'
  } catch (error) {
    feedback.error = error?.payload?.detail || '아바타 업로드에 실패했습니다.'
  } finally {
    isUploadingAvatar.value = false
  }
}

const handlePasswordChange = async () => {
  resetFeedback()
  isChangingPassword.value = true
  try {
    const payload = await changePassword({
      current_password: passwordForm.current_password,
      new_password: passwordForm.new_password,
    })
    if (payload?.token) {
      setSession(payload.token, profile.value)
    }
    passwordForm.current_password = ''
    passwordForm.new_password = ''
    feedback.success = '비밀번호가 변경되었습니다.'
  } catch (error) {
    feedback.error =
      error?.payload?.detail ||
      (error?.payload && typeof error.payload === 'object'
        ? Object.values(error.payload).flat().join(' ')
        : '비밀번호를 변경하지 못했습니다.')
  } finally {
    isChangingPassword.value = false
  }
}

const handleDeleteAccount = async () => {
  resetFeedback()
  if (!deleteForm.password) {
    feedback.error = '비밀번호를 입력해 주세요.'
    return
  }
  if (!window.confirm('정말로 계정을 삭제하시겠습니까? 복구할 수 없습니다.')) return
  isDeletingAccount.value = true
  try {
    await deleteAccount({ password: deleteForm.password })
    deleteForm.password = ''
    clearSession()
    feedback.success = '회원 탈퇴가 완료되었습니다.'
  } catch (error) {
    feedback.error =
      error?.payload?.detail ||
      (error?.payload && typeof error.payload === 'object'
        ? Object.values(error.payload).flat().join(' ')
        : '회원 탈퇴 중 오류가 발생했습니다.')
  } finally {
    isDeletingAccount.value = false
  }
}

onMounted(async () => {
  await ensureProfileLoaded()
  if (profile.value) {
    syncProfileForm()
  }
})
</script>

<template>
  <section class="panel">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <div>
        <h2 class="h4 text-light mb-1">계정 관리</h2>
        <p class="text-white-50 mb-0">Token 인증 기반으로 회원정보를 조회·수정합니다.</p>
      </div>
    </div>

    <div v-if="profile" class="row g-4">
      <div class="col-12 col-lg-6">
        <div class="card h-100 border-0">
          <div class="card-body d-flex flex-column gap-3">
            <div class="d-flex justify-content-between align-items-center">
              <h5 class="text-light mb-0">내 계정</h5>
              <button class="btn btn-outline-light btn-sm nav-hover" type="button" @click="handleLogout">로그아웃</button>
            </div>
            <div class="d-flex gap-3 align-items-center">
              <img
                v-if="avatarPreview"
                :src="avatarPreview"
                alt="avatar"
                class="rounded-4 border border-secondary"
                width="72"
                height="72"
              />
              <div>
                <p class="mb-1 text-light fw-semibold">
                  <span v-if="profile.user.first_name">{{ profile.user.first_name }} · </span>@{{ profile.user.username }}
                </p>
                <p class="mb-1 text-white-50">{{ profile.user.email || '이메일 정보 없음' }}</p>
                <p class="mb-0 text-white-50">{{ profile.bio || '소개글이 없습니다.' }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="col-12 col-lg-6">
        <div class="card h-100 border-0">
          <div class="card-body">
            <h5 class="text-light mb-3">프로필 수정</h5>
            <form class="row g-3" autocomplete="off" @submit.prevent="handleProfileUpdate">
              <div class="col-12">
                <label class="form-label text-white-50">표시 이름</label>
                <input v-model="profileForm.display_name" class="form-control" placeholder="공개 이름" />
              </div>
              <div class="col-12">
                <label class="form-label text-white-50">소개</label>
                <textarea v-model="profileForm.bio" class="form-control" rows="3" placeholder="자기 소개를 입력해 주세요"></textarea>
              </div>
              <div class="col-12">
                <button class="btn btn-primary nav-hover" :disabled="isUpdatingProfile" type="submit">
                  <span v-if="isUpdatingProfile">저장 중...</span>
                  <span v-else>프로필 저장</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
      <div class="col-12 col-lg-6">
        <div class="card border-0 h-100">
          <div class="card-body d-flex flex-column gap-3">
            <h5 class="text-light">아바타</h5>
            <input class="form-control" type="file" accept="image/*" @change="handleAvatarChange" />
            <small class="text-white-50">※ 최대 200KB 이미지 파일만 업로드할 수 있습니다.</small>
            <button
              class="btn btn-outline-light nav-hover"
              :disabled="isUploadingAvatar || !avatarFile"
              type="button"
              @click="handleAvatarUpload"
            >
              <span v-if="isUploadingAvatar">업로드 중...</span>
              <span v-else>아바타 업로드</span>
            </button>
          </div>
        </div>
      </div>
      <div class="col-12 col-lg-6">
        <div class="card border-0 h-100">
          <div class="card-body">
            <h5 class="text-light mb-3">비밀번호 변경</h5>
            <form class="row g-3" autocomplete="off" @submit.prevent="handlePasswordChange">
              <div class="col-12">
                <label class="form-label text-white-50">현재 비밀번호</label>
                <input v-model="passwordForm.current_password" class="form-control" type="password" required />
              </div>
              <div class="col-12">
                <label class="form-label text-white-50">새 비밀번호</label>
                <input v-model="passwordForm.new_password" class="form-control" type="password" minlength="8" required />
              </div>
              <div class="col-12">
                <button class="btn btn-primary nav-hover" :disabled="isChangingPassword" type="submit">
                  <span v-if="isChangingPassword">변경 중...</span>
                  <span v-else>비밀번호 변경</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
      <div class="col-12 col-lg-6">
        <div class="card border-0 h-100">
          <div class="card-body">
            <h5 class="text-light mb-3">회원 탈퇴</h5>
            <p class="text-white-50 small">계정과 모든 연관 데이터를 삭제합니다. 삭제 후에는 복구할 수 없습니다.</p>
            <form class="row g-3" autocomplete="off" @submit.prevent="handleDeleteAccount">
              <div class="col-12">
                <label class="form-label text-white-50">비밀번호 확인</label>
                <input v-model="deleteForm.password" class="form-control" type="password" required />
              </div>
              <div class="col-12 d-flex gap-3 flex-wrap">
                <button class="btn btn-danger nav-hover" :disabled="isDeletingAccount" type="submit">
                  <span v-if="isDeletingAccount">삭제 중...</span>
                  <span v-else>회원 탈퇴</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="row g-4">
      <div class="col-12 col-lg-6">
        <div class="card border-0 h-100">
          <div class="card-body">
            <h5 class="text-light mb-3">회원가입</h5>
            <form class="row g-3" autocomplete="off" @submit.prevent="handleRegister">
              <div class="col-12">
                <label class="form-label text-white-50">아이디</label>
                <input v-model="registerForm.username" class="form-control" placeholder="예) new_user" minlength="3" required />
              </div>
              <div class="col-12">
                <label class="form-label text-white-50">이름</label>
                <input
                  v-model="registerForm.name"
                  class="form-control"
                  placeholder="한글 2~5글자"
                  pattern="^[가-힣]{2,5}$"
                  required
                />
              </div>
              <div class="col-12">
                <label class="form-label text-white-50">이메일</label>
                <input v-model="registerForm.email" class="form-control" type="email" placeholder="you@example.com" required />
              </div>
              <div class="col-12">
                <label class="form-label text-white-50">비밀번호</label>
                <input
                  v-model="registerForm.password"
                  class="form-control"
                  type="password"
                  placeholder="8자 이상"
                  minlength="8"
                  required
                />
              </div>
              <div class="col-12">
                <button class="btn btn-primary nav-hover" :disabled="isRegistering" type="submit">
                  <span v-if="isRegistering">가입 중...</span>
                  <span v-else>회원가입</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      <div class="col-12 col-lg-6">
        <div class="card border-0 h-100">
          <div class="card-body">
            <h5 class="text-light mb-3">로그인</h5>
            <form class="row g-3" autocomplete="off" @submit.prevent="handleLogin">
              <div class="col-12">
                <label class="form-label text-white-50">아이디</label>
                <input v-model="loginForm.username" class="form-control" placeholder="아이디를 입력하세요" required />
              </div>
              <div class="col-12">
                <label class="form-label text-white-50">비밀번호</label>
                <input
                  v-model="loginForm.password"
                  class="form-control"
                  type="password"
                  placeholder="비밀번호를 입력하세요"
                  required
                />
              </div>
              <div class="col-12">
                <button class="btn btn-outline-light nav-hover" :disabled="isLoggingIn" type="submit">
                  <span v-if="isLoggingIn">로그인 중...</span>
                  <span v-else>로그인</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>

    <p v-if="feedback.success" class="mt-4 text-success text-center fw-semibold">{{ feedback.success }}</p>
    <p v-if="feedback.error" class="mt-2 text-danger text-center fw-semibold">{{ feedback.error }}</p>
  </section>
</template>
