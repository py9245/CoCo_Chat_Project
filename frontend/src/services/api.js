const resolveRuntimeBase = () => {
  if (typeof window === 'undefined') return null
  if (window.API_BASE_URL) return window.API_BASE_URL
  if (window.location.hostname?.endsWith('github.io')) {
    return 'https://15-164-232-40.nip.io/api'
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

export const fetchHealth = () => request('/healthz')
export const fetchMessages = () => request('/messages')

export const registerUser = (body) => request('/auth/register', { method: 'POST', body })
export const loginUser = (body) => request('/auth/login', { method: 'POST', body })
export const fetchProfile = () => request('/auth/profile')
export const logoutUser = () => request('/auth/logout', { method: 'POST' })

const buildQueryString = (params = {}) => {
  const searchParams = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return
    searchParams.set(key, value)
  })
  const query = searchParams.toString()
  return query ? `?${query}` : ''
}

export const fetchChatMessages = (params) =>
  request(`/chat/messages${buildQueryString(params)}`)

export const postChatMessage = (body) =>
  request('/chat/messages', { method: 'POST', body })
