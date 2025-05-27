<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import Dashboard from './components/Dashboard.vue'

const data = ref(null)
const API = 'https://sorting-dashboard-api-208732756826.europe-west4.run.app/dashboard'

/* 1) pull once on mount — or open a websocket for realtime */
onMounted(async () => {
  const res = await axios.get(API)
  data.value = res.data
  setBodyColor(data.value.status)
})

/* 2) helper to keep body class in sync */
function setBodyColor(status) {
  document.body.classList.remove('status-good', 'status-risk', 'status-bad')
  document.body.classList.add(`status-${status}`)
}
</script>

<template>
  <Dashboard v-if="data" :data="data" />
  <p v-else class="text-center mt-10">Loading…</p>
</template>
