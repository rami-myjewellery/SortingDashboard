<!-- src/views/NextDayProgress.vue -->
<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import axios from 'axios'
import { useRoute } from 'vue-router'

interface DockLoad {
  id: string
  load_code: string
  carrier: string
  dock: string
  work_mode: string
  scheduling: string
  scheduled_time: string
  status: string
  picks_done: number
  picks_total: number
  picks_percentage: number
  hds_loaded: number
  hds_total: number
  load_percentage: number
  urgency: 'critical' | 'warning' | 'upcoming' | 'scheduled'
}

interface DashboardData {
  title: string
  status: 'good' | 'risk' | 'bad'
  kpis: Array<{ label: string; value: number | string; unit: string }>
  loads?: DockLoad[]
}

const API = 'https://sorting-dashboard-api-208732756826.europe-west4.run.app/dashboard/NextDayProgress'

// ── Default Mock Dataset (Reflex Dock Management Screenshot) ─────────────────
const DEFAULT_LOADS: DockLoad[] = [
  {
    id: 'load-b2ceu',
    load_code: '23/10/26 B2CEU',
    carrier: 'B2C Europe',
    dock: 'DOCK-003',
    work_mode: 'LOA - LOAD',
    scheduling: '18h00 - 19h00',
    scheduled_time: '18:00',
    status: 'Carrier expected',
    picks_done: 94,
    picks_total: 104,
    picks_percentage: 90.4,
    hds_loaded: 0,
    hds_total: 48,
    load_percentage: 0.0,
    urgency: 'critical'
  },
  {
    id: 'load-pnlpar',
    load_code: '23/10/26 PNLPAR',
    carrier: 'PostNL Pakketten',
    dock: 'DOCK-003',
    work_mode: 'LOA - LOAD',
    scheduling: '23h00 - 23h45',
    scheduled_time: '23:00',
    status: 'Picking in progress',
    picks_done: 582,
    picks_total: 970,
    picks_percentage: 60.0,
    hds_loaded: 0,
    hds_total: 64,
    load_percentage: 0.0,
    urgency: 'warning'
  },
  {
    id: 'load-pnleur',
    load_code: '23/10/26 PNLEUR',
    carrier: 'PostNL Europe',
    dock: 'DOCK-004',
    work_mode: 'LOA - LOAD',
    scheduling: '23h00 - 23h45',
    scheduled_time: '23:00',
    status: 'Picking in progress',
    picks_done: 296,
    picks_total: 510,
    picks_percentage: 58.0,
    hds_loaded: 0,
    hds_total: 36,
    load_percentage: 0.0,
    urgency: 'warning'
  },
  {
    id: 'load-dhlfy',
    load_code: '23/10/26 DHLFY',
    carrier: 'DHL Parcel',
    dock: 'DOCK-005',
    work_mode: 'LOA - LOAD',
    scheduling: '23h30 - 00h30',
    scheduled_time: '23:30',
    status: 'Picking started',
    picks_done: 145,
    picks_total: 520,
    picks_percentage: 27.9,
    hds_loaded: 0,
    hds_total: 42,
    load_percentage: 0.0,
    urgency: 'upcoming'
  },
  {
    id: 'load-inthq',
    load_code: '23/10/26 INTHQ',
    carrier: 'Internal HQ Transfer',
    dock: 'DOCK-008',
    work_mode: 'LOA - LOAD',
    scheduling: '00h00 - 01h00',
    scheduled_time: '00:00',
    status: 'Scheduled',
    picks_done: 12,
    picks_total: 150,
    picks_percentage: 8.0,
    hds_loaded: 0,
    hds_total: 24,
    load_percentage: 0.0,
    urgency: 'scheduled'
  }
]

const data = ref<DashboardData | null>(null)
const loads = computed<DockLoad[]>(() => {
  const raw = data.value?.loads?.length ? data.value.loads : DEFAULT_LOADS
  // Guarantee chronological sort: earliest scheduled time first
  return [...raw].sort((a, b) => {
    // 00:00 belongs at night (after 23:30)
    const normTime = (t: string) => {
      const [h, m] = t.split(':').map(Number)
      return h < 6 ? (h + 24) * 60 + m : h * 60 + m
    }
    return normTime(a.scheduled_time) - normTime(b.scheduled_time)
  })
})

// Current live time
const currentTime = ref(new Date().toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit', second: '2-digit' }))
let timerInterval: any = null

const nextUpcoming = computed(() => loads.value[0] ?? null)

const totalRemainingPicks = computed(() => {
  return loads.value.reduce((acc, l) => acc + (l.picks_total - l.picks_done), 0)
})

const totalRemainingHds = computed(() => {
  return loads.value.reduce((acc, l) => acc + (l.hds_total - l.hds_loaded), 0)
})

const overallPickPercentage = computed(() => {
  const done = loads.value.reduce((acc, l) => acc + l.picks_done, 0)
  const total = loads.value.reduce((acc, l) => acc + l.picks_total, 0)
  return total > 0 ? Math.round((done / total) * 100) : 0
})

const fetchData = async () => {
  try {
    const res = await axios.get(API)
    data.value = res.data
  } catch (err) {
    // Fall back smoothly to mock dataset
    if (!data.value) {
      data.value = {
        title: 'Next Day Cut-Off & Loading',
        status: 'risk',
        kpis: [],
        loads: DEFAULT_LOADS
      }
    }
  }
}

onMounted(() => {
  fetchData()
  const id = setInterval(fetchData, 6_000)
  timerInterval = setInterval(() => {
    currentTime.value = new Date().toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  }, 1000)

  onBeforeUnmount(() => {
    clearInterval(id)
    if (timerInterval) clearInterval(timerInterval)
  })
})

function urgencyClass(urgency: string) {
  switch (urgency) {
    case 'critical': return 'urgency-critical'
    case 'warning': return 'urgency-warning'
    case 'upcoming': return 'urgency-upcoming'
    default: return 'urgency-scheduled'
  }
}
</script>

<template>
  <div class="nextday-dashboard">
    <!-- Header -->
    <header class="nextday-header">
      <div class="header-left">
        <span class="badge-live">LIVE DOCK STATUS</span>
        <h1>Next Day Progress</h1>
        <span class="clock-display">{{ currentTime }}</span>
      </div>
      <div class="header-kpis">
        <div class="header-kpi-card highlight">
          <span class="kpi-title">EERSTVOLGEND VERTREK</span>
          <span class="kpi-value">{{ nextUpcoming ? `${nextUpcoming.scheduled_time} · ${nextUpcoming.carrier}` : '—' }}</span>
        </div>
        <div class="header-kpi-card">
          <span class="kpi-title">OPEN PICKS</span>
          <span class="kpi-value">{{ totalRemainingPicks.toLocaleString('nl-NL') }} <small>picks</small></span>
        </div>
        <div class="header-kpi-card">
          <span class="kpi-title">NOG TE LADEN</span>
          <span class="kpi-value">{{ totalRemainingHds.toLocaleString('nl-NL') }} <small>HDs</small></span>
        </div>
        <div class="header-kpi-card">
          <span class="kpi-title">TOTALE GEREEDHEID</span>
          <span class="kpi-value">{{ overallPickPercentage }}%</span>
        </div>
      </div>
    </header>

    <!-- Main Content: Chronological List of Departures -->
    <main class="loads-container">
      <div
        v-for="(load, index) in loads"
        :key="load.id"
        class="load-card"
        :class="[urgencyClass(load.urgency), { 'is-next': index === 0 }]"
      >
        <!-- Next up tag -->
        <div v-if="index === 0" class="next-tag">
          ⚡ EERSTVOLGEND VERTREK
        </div>

        <div class="card-grid">
          <!-- Column 1: Time & Dock -->
          <div class="col-meta">
            <div class="time-block">
              <span class="time-primary">{{ load.scheduled_time }}</span>
              <span class="time-window">{{ load.scheduling }}</span>
            </div>
            <div class="dock-badge">{{ load.dock }}</div>
          </div>

          <!-- Column 2: Carrier & Load ID -->
          <div class="col-carrier">
            <div class="carrier-name">{{ load.carrier }}</div>
            <div class="load-code">
              <span class="code-pill">{{ load.load_code }}</span>
              <span class="status-pill" :class="'status-' + load.urgency">{{ load.status }}</span>
            </div>
          </div>

          <!-- Column 3: Pick Batch Progress (Yellow/Amber) -->
          <div class="col-progress pick-progress">
            <div class="progress-labels">
              <span class="prog-title">
                <span class="dot-indicator dot-pick"></span>
                Pick Batch
              </span>
              <span class="prog-values">
                <strong>{{ load.picks_done }}</strong> / {{ load.picks_total }} picks
                <span class="pct-badge">{{ Math.round(load.picks_percentage) }}%</span>
              </span>
            </div>
            <div class="progress-track">
              <div
                class="progress-fill fill-pick"
                :style="{ width: `${Math.min(100, Math.max(0, load.picks_percentage))}%` }"
              ></div>
            </div>
          </div>

          <!-- Column 4: Loading (HDs) Progress (Blue/Cyan) -->
          <div class="col-progress load-progress">
            <div class="progress-labels">
              <span class="prog-title">
                <span class="dot-indicator dot-load"></span>
                Laden (HDs)
              </span>
              <span class="prog-values">
                <strong>{{ load.hds_loaded }}</strong> / {{ load.hds_total }} HDs
                <span class="pct-badge">{{ Math.round(load.load_percentage) }}%</span>
              </span>
            </div>
            <div class="progress-track">
              <div
                class="progress-fill fill-load"
                :style="{ width: `${Math.min(100, Math.max(0, load.load_percentage))}%` }"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.nextday-dashboard {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  background: #0f172a;
  color: #f8fafc;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  overflow: hidden;
  box-sizing: border-box;
}

/* Header */
.nextday-header {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5vh 2vw;
  background: #1e293b;
  border-bottom: 2px solid #334155;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
  gap: 2vw;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1.2vw;
}

.header-left h1 {
  margin: 0;
  font-size: clamp(1.4rem, 2.2vw, 2.4rem);
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #ffffff;
}

.badge-live {
  background: #ef4444;
  color: white;
  font-size: 0.75rem;
  font-weight: 800;
  padding: 4px 8px;
  border-radius: 6px;
  letter-spacing: 0.05em;
  animation: pulse-badge 2s infinite;
}

@keyframes pulse-badge {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.clock-display {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: clamp(1.1rem, 1.6vw, 1.8rem);
  color: #94a3b8;
  font-weight: 600;
  padding-left: 0.8vw;
  border-left: 1px solid #475569;
}

.header-kpis {
  display: flex;
  align-items: center;
  gap: 1.2vw;
}

.header-kpi-card {
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 10px;
  padding: 0.8vh 1.2vw;
  display: flex;
  flex-direction: column;
  min-width: 140px;
}

.header-kpi-card.highlight {
  border-color: #f59e0b;
  background: rgba(245, 158, 11, 0.1);
}

.kpi-title {
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #94a3b8;
  font-weight: 600;
}

.header-kpi-card.highlight .kpi-title {
  color: #fbbf24;
}

.kpi-value {
  font-size: clamp(1.1rem, 1.5vw, 1.6rem);
  font-weight: 800;
  color: #f8fafc;
  line-height: 1.2;
  margin-top: 2px;
}

.kpi-value small {
  font-size: 0.8rem;
  font-weight: 500;
  color: #94a3b8;
}

/* Loads list */
.loads-container {
  flex: 1 1 0;
  padding: 1.8vh 2vw;
  display: flex;
  flex-direction: column;
  gap: 1.4vh;
  overflow-y: auto;
}

.load-card {
  position: relative;
  background: #1e293b;
  border: 1.5px solid #334155;
  border-radius: 14px;
  padding: 1.8vh 1.8vw;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
  transition: transform 0.15s ease, border-color 0.15s ease;
}

.load-card.is-next {
  border-color: #f59e0b;
  background: linear-gradient(90deg, rgba(245, 158, 11, 0.08) 0%, rgba(30, 41, 59, 1) 40%);
  box-shadow: 0 6px 20px rgba(245, 158, 11, 0.18);
}

.next-tag {
  position: absolute;
  top: -10px;
  left: 20px;
  background: #f59e0b;
  color: #0f172a;
  font-size: 0.72rem;
  font-weight: 900;
  padding: 2px 10px;
  border-radius: 12px;
  letter-spacing: 0.04em;
  box-shadow: 0 2px 6px rgba(0,0,0,0.3);
}

.card-grid {
  display: grid;
  grid-template-columns: 140px 1.4fr 1.6fr 1.6fr;
  align-items: center;
  gap: 2vw;
}

/* Col 1: Time */
.col-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.time-primary {
  font-size: clamp(1.8rem, 2.6vw, 3rem);
  font-weight: 800;
  line-height: 1;
  color: #ffffff;
  font-family: ui-monospace, SFMono-Regular, monospace;
}

.time-window {
  font-size: 0.75rem;
  color: #94a3b8;
  white-space: nowrap;
}

.dock-badge {
  display: inline-block;
  align-self: flex-start;
  margin-top: 4px;
  background: #334155;
  color: #cbd5e1;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 6px;
  letter-spacing: 0.04em;
}

/* Col 2: Carrier */
.col-carrier {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.carrier-name {
  font-size: clamp(1.2rem, 1.8vw, 2rem);
  font-weight: 700;
  color: #ffffff;
  line-height: 1.2;
}

.load-code {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.code-pill {
  font-family: ui-monospace, SFMono-Regular, monospace;
  font-size: 0.8rem;
  background: rgba(255, 255, 255, 0.08);
  padding: 2px 8px;
  border-radius: 6px;
  color: #cbd5e1;
}

.status-pill {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 6px;
}

.status-critical {
  background: rgba(239, 68, 68, 0.2);
  color: #fca5a5;
  border: 1px solid rgba(239, 68, 68, 0.4);
}

.status-warning {
  background: rgba(245, 158, 11, 0.2);
  color: #fde68a;
  border: 1px solid rgba(245, 158, 11, 0.4);
}

.status-upcoming {
  background: rgba(59, 130, 246, 0.2);
  color: #93c5fd;
  border: 1px solid rgba(59, 130, 246, 0.4);
}

.status-scheduled {
  background: rgba(148, 163, 184, 0.2);
  color: #cbd5e1;
}

/* Col 3 & 4: Progress Bars */
.col-progress {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.progress-labels {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.85rem;
}

.prog-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: #cbd5e1;
}

.dot-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.dot-pick {
  background: #f59e0b;
  box-shadow: 0 0 6px rgba(245, 158, 11, 0.8);
}

.dot-load {
  background: #0ea5e9;
  box-shadow: 0 0 6px rgba(14, 165, 233, 0.8);
}

.prog-values {
  color: #94a3b8;
  display: flex;
  align-items: center;
  gap: 6px;
}

.prog-values strong {
  color: #ffffff;
}

.pct-badge {
  background: #334155;
  color: #f8fafc;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 4px;
}

.progress-track {
  height: 18px;
  background: #0f172a;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid #334155;
  position: relative;
}

.progress-fill {
  height: 100%;
  border-radius: 10px;
  transition: width 0.4s ease;
}

.fill-pick {
  background: linear-gradient(90deg, #d97706 0%, #f59e0b 100%);
  box-shadow: 0 0 10px rgba(245, 158, 11, 0.4);
}

.fill-load {
  background: linear-gradient(90deg, #0284c7 0%, #38bdf8 100%);
  box-shadow: 0 0 10px rgba(14, 165, 233, 0.4);
}

/* Responsiveness for smaller screens */
@media (max-width: 900px) {
  .card-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  .nextday-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
