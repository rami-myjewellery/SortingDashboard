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

const shouldHideBackground = (route) => {
  const raw = route?.query?.bg
  if (raw === undefined) return false
  const val = Array.isArray(raw) ? raw[0] : raw
  return ['0', 'false', 'no', 'off'].includes(String(val).toLowerCase())
}

const syncBackgroundClass = (route) => {
  if (shouldHideBackground(route)) {
    html.classList.add('no-bg')
  } else {
    html.classList.remove('no-bg')
  }
}

// keep synced on navigation and first load
router.afterEach((to) => {
  syncDetailsClass(to)
  syncBackgroundClass(to)
})
router.isReady().then(() => {
  const route = router.currentRoute.value
  syncDetailsClass(route)
  syncBackgroundClass(route)
})

createApp(App).use(router).mount('#app')
