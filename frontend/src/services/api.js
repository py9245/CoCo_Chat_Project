const resolveRuntimeBase = () => {
  if (typeof window === 'undefined') return null
  const stored = (() => {
    try {
      return window.localStorage?.getItem('API_BASE_URL') || null
    } catch {
      return null
    }
  })()
  if (stored) return stored
  if (window.API_BASE_URL) return window.API_BASE_URL
  if (window.location.hostname?.includes('github.io') || window.location.hostname?.includes('githubusercontent.com')) {
    return 'https://3-37-130-181.nip.io/api'
  }
  if (window.location.origin) {
    return `${window.location.origin}/api`
  }
  return null
}

const buildBaseUrl = () => {
  const fallback = '/api'
  const raw = import.meta.env.VITE_API_BASE_URL ?? resolveRuntimeBase() ?? fallback
  const normalized = raw.endsWith('/') ? raw.slice(0, -1) : raw
  return normalized || fallback
}

const API_BASE_URL = buildBaseUrl()
export const getApiBaseUrl = () => API_BASE_URL

const buildUrl = (path) => {
  const cleaned = path.startsWith('/') ? path : `/${path}`
  return `${API_BASE_URL}${cleaned}`
}

const TOKEN_STORAGE_KEY = 'codex_auth_token'
let runtimeToken = null

const readStoredToken = () => {
  if (runtimeToken) return runtimeToken
  if (typeof window === 'undefined') return null
  try {
    runtimeToken = window.localStorage?.getItem(TOKEN_STORAGE_KEY) || null
  } catch {
    runtimeToken = null
  }
  return runtimeToken
}

export const saveAuthToken = (token) => {
  runtimeToken = token || null
  if (typeof window !== 'undefined' && window.localStorage) {
    if (runtimeToken) {
      window.localStorage.setItem(TOKEN_STORAGE_KEY, runtimeToken)
    } else {
      window.localStorage.removeItem(TOKEN_STORAGE_KEY)
    }
  }
  return runtimeToken
}

export const loadAuthToken = () => runtimeToken || readStoredToken()
export const clearAuthToken = () => saveAuthToken(null)

const buildOptions = (method, body) => {
  const headers = {
    Accept: 'application/json',
  }
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
  }
  const token = loadAuthToken()
  if (token) {
    headers.Authorization = `Token ${token}`
  }
  return {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  }
}

const buildAuthHeaders = () => {
  const headers = {
    Accept: 'application/json',
  }
  const token = loadAuthToken()
  if (token) {
    headers.Authorization = `Token ${token}`
  }
  return headers
}

async function request(path, { method = 'GET', body } = {}) {
  const response = await fetch(buildUrl(path), buildOptions(method, body))
  const rawText = await response.text()
  let payload = null
  if (rawText) {
    try {
      payload = JSON.parse(rawText)
    } catch {
      payload = null
    }
  }

  if (!response.ok) {
    const message = payload?.detail || `Request failed: ${response.status}`
    const error = new Error(message)
    error.status = response.status
    error.payload = payload
    throw error
  }

  return payload
}

async function requestMultipart(path, { method = 'POST', body }) {
  const response = await fetch(buildUrl(path), {
    method,
    headers: buildAuthHeaders(),
    body,
  })
  const rawText = await response.text()
  let payload = null
  if (rawText) {
    try {
      payload = JSON.parse(rawText)
    } catch {
      payload = null
    }
  }

  if (!response.ok) {
    const message = payload?.detail || `Request failed: ${response.status}`
    const error = new Error(message)
    error.status = response.status
    error.payload = payload
    throw error
  }

  return payload
}

export const fetchHealth = () => request('/healthz')
export const fetchHomeOverview = () => request('/pages/home')

export const registerUser = (body) => request('/accounts/register', { method: 'POST', body })
export const loginUser = (body) => request('/accounts/login', { method: 'POST', body })
export const fetchProfile = () => request('/accounts/profile')
export const logoutUser = () => request('/accounts/logout', { method: 'POST' })
export const updateProfile = (body) => request('/accounts/profile/update', { method: 'PATCH', body })
export const changePassword = (body) => request('/accounts/profile/password', { method: 'POST', body })
export const uploadAvatar = (formData) => requestMultipart('/accounts/profile/avatar', { method: 'POST', body: formData })
export const deleteAccount = (body) => request('/accounts/profile/delete', { method: 'POST', body })

export const fetchPosts = () => request('/boards/posts')
export const createPost = (formData) => requestMultipart('/boards/posts', { method: 'POST', body: formData })
export const updatePost = (id, formData) =>
  requestMultipart(`/boards/posts/${id}`, { method: 'PATCH', body: formData })
export const deletePost = (id) => request(`/boards/posts/${id}`, { method: 'DELETE' })

const buildQueryString = (params = {}) => {
  const searchParams = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return
    searchParams.set(key, value)
  })
  const query = searchParams.toString()
  return query ? `?${query}` : ''
}

export const fetchChatRooms = () => request('/chat/rooms')
export const createChatRoom = (body) => request('/chat/rooms', { method: 'POST', body })
export const joinChatRoom = (body) => request('/chat/rooms/join', { method: 'POST', body })
export const leaveChatRoom = (roomId) => request(`/chat/rooms/${roomId}/leave`, { method: 'POST' })
export const fetchChatMessages = (roomId, params) =>
  request(`/chat/rooms/${roomId}/messages${buildQueryString(params)}`)
export const postChatMessage = (roomId, body) =>
  request(`/chat/rooms/${roomId}/messages`, { method: 'POST', body })

export const fetchRandomChatState = (params) => request(`/random-chat/state${buildQueryString(params)}`)
export const joinRandomChatQueue = () => request('/random-chat/queue', { method: 'POST' })
export const leaveRandomChatQueue = () => request('/random-chat/queue', { method: 'DELETE' })
export const requestRandomChatMatch = () => request('/random-chat/match', { method: 'POST' })
export const fetchRandomChatMessages = (params) =>
  request(`/random-chat/messages${buildQueryString(params)}`)
export const postRandomChatMessage = (body) => request('/random-chat/messages', { method: 'POST', body })
