import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'
import './style.css'

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

restoreGitHubPagesPath()

const app = createApp(App)
app.use(router)
app.mount('#app')
