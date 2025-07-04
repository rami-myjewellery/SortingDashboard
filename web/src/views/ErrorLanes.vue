<!-- src/views/DashboardView.vue -->
<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import axios   from 'axios'
import Dashboard from '@/components/Dashboard.vue'   // keep ✅
import { useRoute } from 'vue-router'
const API = 'https://sorting-dashboard-api-208732756826.europe-west4.run.app/dashboard/ErrorLanes'

// const API = 'http://127.0.0.1:5001/dashboard/Sorting'

const data = ref(null)
const route = useRoute()
const showPeople = route.query.bool === 'true'

// fetch loop ───────────────────────────────────────────────
const fetchData = async () => {
  try {
    const res = await axios.get(API)
    data.value = res.data
    setBodyColor(data.value.status)
  } catch (err) {
    console.error('Failed to fetch dashboard data:', err)
  }
}

onMounted(() => {
  fetchData()
  const id = setInterval(fetchData, 5_000)
  onBeforeUnmount(() => clearInterval(id))
})

// helper ───────────────────────────────────────────────────
function setBodyColor(status: string) {
  document.body.classList.remove('status-good', 'status-risk', 'status-bad')
  document.body.classList.add(`status-${status}`)
}
</script>

<template>
  <Dashboard v-if="data" :data="data" :show-people="showPeople" />
  <p v-else class="text-center mt-10">Loading…</p>
</template>
