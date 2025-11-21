import { createApp } from 'vue'
import App from './App.vue'
import './assets/base.css'   // global styles
import router from './router'

const html = document.documentElement

// decide whether to show inactivity details based on URL query
const shouldShowDetails = (route) => {
  const raw =
      route?.query?.showInactive ??
      route?.query?.showInactivity ??
      route?.query?.showDetails ??
      route?.query?.details

  // default: show details when no flag provided
  if (raw === undefined) return true

  const val = Array.isArray(raw) ? raw[0] : raw
  return ['1', 'true', 'yes', 'on'].includes(String(val).toLowerCase())
}

const syncDetailsClass = (route) => {
  if (shouldShowDetails(route)) {
    html.classList.add('show-details')
  } else {
    html.classList.remove('show-details')
  }
}

// keep synced on navigation and first load
router.afterEach((to) => syncDetailsClass(to))
router.isReady().then(() => syncDetailsClass(router.currentRoute.value))

createApp(App).use(router).mount('#app')
