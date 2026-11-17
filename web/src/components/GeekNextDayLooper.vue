<script setup lang="ts">
import { ref, computed, watchEffect, onMounted, onBeforeUnmount } from 'vue'
import axios from 'axios'
import { useRoute } from 'vue-router'
import Dashboard from '@/components/Dashboard.vue'
import NextDayProgress from '@/views/NextDayProgress.vue'

const props = defineProps<{
  api: string
  phaseOffset: number
}>()

const ROTATION_INTERVAL_MS = 30_000

const route = useRoute()
const data = ref<any>(null)
const geekStatus = ref<'good' | 'risk' | 'bad'>('good')
const nextDayStatus = ref<'good' | 'risk' | 'bad'>('good')
const showPeople = computed(() => route.query.bool === 'true')

// Determine whether this screen should run the 30s NextDay rotation loop:
// - Disabled when ?loop=false (e.g. inside WarehouseMetaDashboard) or when embedded in an iframe
// - Enabled on standalone ("specifieke") Geek TV screens (or when ?loop=true)
const shouldLoop = computed(() => {
  const raw = route.query.loop
  const val = Array.isArray(raw) ? raw[0] : raw
  if (val !== undefined && val !== null) {
    const norm = String(val).trim().toLowerCase()
    if (['1', 'true', 'yes', 'on'].includes(norm)) return true
    if (['0', 'false', 'no', 'off'].includes(norm)) return false
  }
  if (typeof window === 'undefined') return false
  try {
    return window.self === window.top
  } catch {
    return false
  }
})

// Synchronize rotation across separate physical TV screens using wall-clock 30s slots
const currentSlot = ref(Math.floor(Date.now() / ROTATION_INTERVAL_MS) % 2)
const showNextDay = computed(() => {
  if (!shouldLoop.value) return false
  return (currentSlot.value + props.phaseOffset) % 2 === 1
})

function normalizeStatus(raw?: string): 'good' | 'risk' | 'bad' {
  if (raw === 'bad' || raw === 'risk' || raw === 'good') return raw
  return 'good'
}

function setBodyColor(status: string) {
  document.body.classList.remove('status-good', 'status-risk', 'status-bad')
  document.body.classList.add(`status-${status}`)
}

watchEffect(() => {
  const activeStatus = showNextDay.value ? nextDayStatus.value : geekStatus.value
  setBodyColor(activeStatus)
})

const fetchData = async () => {
  try {
    const res = await axios.get(props.api)
    data.value = res.data
    geekStatus.value = normalizeStatus(res.data?.status)
  } catch (err) {
    console.error('Failed to fetch dashboard data:', err)
  }
}

onMounted(() => {
  fetchData()
  const fetchTimer = setInterval(fetchData, 5_000)
  const slotTimer = setInterval(() => {
    currentSlot.value = Math.floor(Date.now() / ROTATION_INTERVAL_MS) % 2
  }, 250)

  onBeforeUnmount(() => {
    clearInterval(fetchTimer)
    clearInterval(slotTimer)
  })
})
</script>

<template>
  <!-- Standalone ("specifieke") TV screen: 30s alternating 3D flip with NextDayProgress -->
  <div v-if="shouldLoop" class="loop-stage">
    <div class="loop-flip-inner" :class="{ 'is-flipped': showNextDay }">
      <!-- Front face: Geek Dashboard (GeekInbound or GeekPicking) -->
      <div class="loop-face loop-face-front" :class="`face-${geekStatus}`">
        <Dashboard v-if="data" :data="data" :show-people="showPeople" />
        <p v-else class="loading-msg">Loading…</p>
      </div>

      <!-- Back face: Next Day Progress -->
      <div class="loop-face loop-face-back" :class="`face-${nextDayStatus}`">
        <NextDayProgress
          :managed-status="true"
          @status-change="nextDayStatus = $event"
        />
      </div>
    </div>
  </div>

  <!-- Embedded in Meta Dashboard (?loop=false / iframe): static Geek view only -->
  <template v-else>
    <Dashboard v-if="data" :data="data" :show-people="showPeople" />
    <p v-else class="loading-msg">Loading…</p>
  </template>
</template>

<style scoped>
.loop-stage {
  position: fixed;
  inset: 0;
  perspective: 1800px;
  background: #06182c;
  overflow: hidden;
}

.loop-flip-inner {
  position: relative;
  width: 100%;
  height: 100%;
  transform-style: preserve-3d;
}

@media (prefers-reduced-motion: no-preference) {
  .loop-flip-inner {
    transition: transform 0.85s cubic-bezier(0.4, 0, 0.2, 1);
  }
}

.loop-flip-inner.is-flipped {
  transform: rotateY(180deg);
}

.loop-flip-inner.is-flipped .loop-face-front {
  pointer-events: none;
}

.loop-flip-inner:not(.is-flipped) .loop-face-back {
  pointer-events: none;
}

.loop-face {
  position: absolute;
  inset: 0;
  display: block;
  overflow: hidden;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
  transition: background 0.3s;
}

.loop-face::before {
  content: "";
  position: absolute;
  inset: 0;
  background: var(--bg-url) center bottom / auto 80% no-repeat;
  filter: grayscale(100%) brightness(1.35) contrast(1);
  mix-blend-mode: multiply;
  pointer-events: none;
  z-index: 0;
}

:global(html.no-bg) .loop-face::before {
  display: none;
}

.loop-face > :deep(*) {
  position: relative;
  z-index: 1;
}

.face-good {
  background: var(--clr-bg-good);
}

.face-risk {
  background: var(--clr-bg-risk);
}

.face-bad {
  background: var(--clr-bg-bad);
}

.loop-face-back {
  transform: rotateY(180deg);
}

.loading-msg {
  text-align: center;
  margin-top: 2.5rem;
}
</style>
