<script setup>
import { ref, onMounted,onBeforeUnmount } from 'vue'
import axios from 'axios'
import Dashboard from './components/Dashboard.vue'
import { useRoute } from 'vue-router'

const data = ref(null)
// const API = 'https://sorting-dashboard-api-208732756826.europe-west4.run.app/dashboard/'
const API = 'http://127.0.0.1:5001/dashboard/'

const route = useRoute()
const showPeople = route.query.bool === 'true'
/* 1) pull once on mount — or open a websocket for realtime */
onMounted(() => {
  const fetchData = async () => {
    try {
      const res = await axios.get(API)
      data.value = res.data
      setBodyColor(data.value.status)
    } catch (err) {
      console.error("Failed to fetch dashboard data:", err)
    }
  }

  // Fetch immediately on mount
  fetchData()

  // Poll every 5 seconds
  const intervalId = setInterval(fetchData, 5000)

  // Optional: clear interval when component unmounts
  onBeforeUnmount(() => {
    clearInterval(intervalId)
  })
})

/* 2) helper to keep body class in sync */
function setBodyColor(status) {
  console.error('setBodyColor', 'status-'+status)
  document.body.classList.remove('status-good', 'status-risk', 'status-bad')
  document.body.classList.add(`status-${status}`)
}
</script>

<template>
  <Dashboard v-if="data" :data="data" />
  <p v-else class="text-center mt-10">Loading…</p>
</template>
