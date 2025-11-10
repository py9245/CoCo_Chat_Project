import { ref } from 'vue'
import { clearAuthToken, fetchProfile, loadAuthToken, saveAuthToken } from '@/services/api'

const authToken = ref(loadAuthToken())
const profile = ref(null)
const initializing = ref(false)
const initialized = ref(false)

const setSession = (token, profilePayload) => {
  if (typeof token !== 'undefined') {
    authToken.value = token ? saveAuthToken(token) : clearAuthToken()
  }
  if (typeof profilePayload !== 'undefined') {
    profile.value = profilePayload || null
  }
}

const clearSession = () => {
  clearAuthToken()
  authToken.value = null
  profile.value = null
}

const ensureProfileLoaded = async () => {
  if (!authToken.value) {
    profile.value = null
    initialized.value = true
    return null
  }
  if (initializing.value) return profile.value
  initializing.value = true
  try {
    const payload = await fetchProfile()
    profile.value = payload?.profile ?? null
  } catch (error) {
    console.warn('프로필 정보를 불러오지 못했습니다.', error)
    clearSession()
  } finally {
    initializing.value = false
    initialized.value = true
  }
  return profile.value
}

export function useSession() {
  return {
    authToken,
    profile,
    initialized,
    setSession,
    clearSession,
    ensureProfileLoaded,
  }
}
