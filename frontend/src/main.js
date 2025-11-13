import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'
import './style.css'

const BASE_STORAGE_KEY = 'codex-spa-base-path'

const persistBasePath = () => {
  if (typeof window === 'undefined') return
  try {
    const rawBase = import.meta.env.BASE_URL || '/'
    const baseWithLeading = rawBase.startsWith('/') ? rawBase : `/${rawBase}`
    const normalized = baseWithLeading.endsWith('/') ? baseWithLeading : `${baseWithLeading}/`
    window.localStorage.setItem(BASE_STORAGE_KEY, normalized)
  } catch (error) {
    console.warn('기본 경로를 저장하지 못했습니다.', error)
  }
}

const restoreGitHubPagesPath = () => {
  const { search, pathname, hash } = window.location
  if (!search.startsWith('?/')) {
    return
  }

  const decodedSegments = search
    .slice(2)
    .split('&')
    .map((segment) => segment.replace(/~and~/g, '&'))

  const path = decodedSegments.shift() ?? ''
  const query = decodedSegments.length ? `?${decodedSegments.join('&')}` : ''
  const basePath = pathname.replace(/\/$/, '')
  const newUrl = `${basePath}/${path}${query}${hash}`

  window.history.replaceState(null, document.title, newUrl)
}

persistBasePath()
restoreGitHubPagesPath()

const app = createApp(App)
app.use(router)
app.mount('#app')
