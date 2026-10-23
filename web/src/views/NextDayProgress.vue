<!-- src/views/NextDayProgress.vue -->
<script setup lang="ts">
import { ref, computed, watchEffect, onMounted, onBeforeUnmount } from 'vue'
import axios from 'axios'
import KpiCard from '@/components/KpiCard.vue'

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

const rawLoads = ref<DockLoad[]>(DEFAULT_LOADS)

// Chronological sort from earliest upcoming departure to latest
const sortedLoads = computed<DockLoad[]>(() => {
  return [...rawLoads.value].sort((a, b) => {
    const normTime = (t: string) => {
      const [h, m] = t.split(':').map(Number)
      return h < 6 ? (h + 24) * 60 + m : h * 60 + m
    }
    return normTime(a.scheduled_time) - normTime(b.scheduled_time)
  })
})

// Earliest scheduled_time (can include 1, 2 or more simultaneous pickups)
const earliestTime = computed(() => sortedLoads.value[0]?.scheduled_time ?? null)

const earliestLoads = computed(() => {
  if (!earliestTime.value) return []
  return sortedLoads.value.filter((l) => l.scheduled_time === earliestTime.value)
})

function isEarliestMoment(load: DockLoad) {
  return earliestTime.value !== null && load.scheduled_time === earliestTime.value
}

// Background status reflects the earliest pickup moment(s)
const computedStatus = computed<'good' | 'risk' | 'bad'>(() => {
  if (!earliestLoads.value.length) return 'good'
  const minPct = Math.min(...earliestLoads.value.map((l) => l.picks_percentage))
  if (minPct >= 80) return 'good'
  if (minPct >= 40) return 'risk'
  return 'bad'
})

const topKpis = computed(() => {
  const remainingPicks = sortedLoads.value.reduce((acc, l) => acc + (l.picks_total - l.picks_done), 0)
  const remainingHds = sortedLoads.value.reduce((acc, l) => acc + (l.hds_total - l.hds_loaded), 0)
  return [
    {
      label: 'Openstaande Picks',
      value: remainingPicks,
      unit: 'picks'
    },
    {
      label: 'Nog te laden op dock',
      value: remainingHds,
      unit: 'HDs'
    }
  ]
})

const historyText = computed(() => {
  if (!earliestLoads.value.length) return ''
  const first = earliestLoads.value[0]
  const carriers = earliestLoads.value.map((l) => `${l.carrier} (${l.dock})`).join(' & ')
  return `Eerstvolgende pickup: ${first.scheduling} · ${carriers}`
})

function setBodyColor(s: string) {
  document.body.classList.remove('status-good', 'status-risk', 'status-bad')
  document.body.classList.add(`status-${s}`)
}

watchEffect(() => {
  setBodyColor(computedStatus.value)
})

const fetchData = async () => {
  try {
    const res = await axios.get(API)
    if (res.data?.loads?.length) {
      rawLoads.value = res.data.loads
    }
  } catch (err) {
    rawLoads.value = DEFAULT_LOADS
  }
}

onMounted(() => {
  setBodyColor(computedStatus.value)
  fetchData()
  const id = setInterval(fetchData, 5_000)
  onBeforeUnmount(() => clearInterval(id))
})

function dialClass(pct: number) {
  if (pct >= 80) return 'good'
  if (pct >= 40) return 'warn'
  return 'bad'
}
</script>

<template>
  <header>Next Day Progress</header>

  <main class="nd-main">
    <!-- Top KPI section: 2 side-by-side KpiCards using the standard component -->
    <section class="kpi-area nd-kpi-area">
      <div class="kpis">
        <KpiCard
          v-for="k in topKpis"
          :key="k.label"
          v-bind="k"
        />
      </div>
    </section>

    <p class="history nd-history">{{ historyText }}</p>

    <!-- Chronological pickup rows from top (earliest) to bottom -->
    <section class="people-list pickup-list">
      <div
        v-for="load in sortedLoads"
        :key="load.id"
        class="person-bar pickup-card"
        :class="[
          { 'is-next': isEarliestMoment(load) },
          `card-${dialClass(load.picks_percentage)}`
        ]"
      >
        <!-- Top row of card: Time badge + Carrier + Dock + Dial -->
        <div class="pickup-top">
          <div class="pickup-left">
            <div
              class="time-badge"
              :class="isEarliestMoment(load) ? `badge-${dialClass(load.picks_percentage)}` : ''"
            >
              <span class="time-main">{{ load.scheduled_time }}</span>
              <span class="time-dock">{{ load.dock }}</span>
            </div>

            <div class="carrier-block">
              <div class="carrier-line">
                <span class="carrier-title">{{ load.carrier }}</span>
                <span
                  v-if="isEarliestMoment(load)"
                  class="next-badge"
                  :class="`badge-${dialClass(load.picks_percentage)}`"
                >
                  EERSTVOLGEND
                </span>
              </div>
              <div class="meta-line">
                <span class="meta-code">{{ load.load_code }}</span>
                <span class="meta-sep">•</span>
                <span>{{ load.scheduling }}</span>
                <span class="meta-sep">•</span>
                <span class="meta-status">{{ load.status }}</span>
              </div>
            </div>
          </div>

          <div
            class="dial pickup-dial"
            :class="dialClass(load.picks_percentage)"
            :style="{ '--value': Math.round(load.picks_percentage) }"
          >
            <span>{{ Math.round(load.picks_percentage) }}%</span>
          </div>
        </div>

        <!-- Bottom row of card: 2 side-by-side progress bars (Pick Batch & Laden HDs) -->
        <div class="pickup-bars">
          <!-- Bar 1: Pick Batch (Amber/Gold like Reflex) -->
          <div class="prog-col">
            <div class="prog-head">
              <span class="prog-label">Pick Batch</span>
              <span class="prog-val">
                <strong>{{ load.picks_done }}</strong> / {{ load.picks_total }}
                ({{ Math.round(load.picks_percentage) }}%)
              </span>
            </div>
            <div class="prog-track">
              <div
                class="prog-fill fill-pick"
                :style="{ width: `${Math.min(100, Math.max(0, load.picks_percentage))}%` }"
              ></div>
            </div>
          </div>

          <!-- Bar 2: Laden HDs (Header Blue) -->
          <div class="prog-col">
            <div class="prog-head">
              <span class="prog-label">Laden HDs</span>
              <span class="prog-val">
                <strong>{{ load.hds_loaded }}</strong> / {{ load.hds_total }}
                ({{ Math.round(load.load_percentage) }}%)
              </span>
            </div>
            <div class="prog-track">
              <div
                class="prog-fill fill-load"
                :style="{ width: `${Math.min(100, Math.max(0, load.load_percentage))}%` }"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </main>
</template>

<style scoped>
.nd-main {
  padding: 1.5vh 2.5vw 2vh 2.5vw;
}

.nd-kpi-area {
  flex: 0 0 18vh;
}

.nd-kpi-area :deep(.kpi-card) {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 1.2vh 1.5vw;
}

.nd-kpi-area :deep(.kpi-value) {
  font-size: clamp(2.5rem, 9vw, 5.5rem);
}

.nd-kpi-area :deep(.kpi-title) {
  font-size: clamp(1.2rem, 3.8vw, 2.4rem);
}

.nd-kpi-area :deep(.kpi-label) {
  font-size: clamp(0.85rem, 2vw, 1.4rem);
}

.nd-history {
  margin: 1vh 0 0.8vh 0;
  font-size: clamp(0.95rem, 2.1vw, 1.5rem);
  font-weight: 600;
}

.pickup-list {
  --person-gap: 1.4vh;
  flex: 1 1 0;
  display: flex;
  flex-direction: column;
  gap: var(--person-gap);
  margin-top: 0.6vh;
}

.pickup-card {
  height: auto;
  min-height: 10.5vh;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: stretch;
  padding: 1.3vh 2.2vw;
  background: rgba(232, 240, 250, 0.94);
  border-radius: 0 0.85rem 0 0;
  border-left: 1vw solid var(--clr-header);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.16);
  box-sizing: border-box;
}

.pickup-card.is-next {
  background: #ffffff;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.28);
}

.pickup-card.is-next.card-good {
  border-left: 1.2vw solid #0b7c4b;
}

.pickup-card.is-next.card-warn {
  border-left: 1.2vw solid #ff9c2a;
}

.pickup-card.is-next.card-bad {
  border-left: 1.2vw solid #d6252c;
}

/* Top part of each pickup card */
.pickup-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5vw;
}

.pickup-left {
  display: flex;
  align-items: center;
  gap: 2vw;
  min-width: 0;
}

.time-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--clr-header);
  color: #ffffff;
  border-radius: 0.5rem;
  padding: 0.4vh 1.4vw;
  min-width: 12vw;
  text-align: center;
  flex-shrink: 0;
}

.badge-good {
  background: #0b7c4b !important;
}

.badge-warn {
  background: #ff9c2a !important;
}

.badge-bad {
  background: #d6252c !important;
}

.time-main {
  font-size: clamp(1.3rem, 3.4vw, 2.3rem);
  font-weight: 800;
  line-height: 1.05;
}

.time-dock {
  font-size: clamp(0.7rem, 1.5vw, 1.05rem);
  font-weight: 700;
  letter-spacing: 0.04em;
  opacity: 0.92;
}

.carrier-block {
  display: flex;
  flex-direction: column;
  gap: 0.25vh;
  min-width: 0;
}

.carrier-line {
  display: flex;
  align-items: center;
  gap: 1.2vw;
}

.carrier-title {
  font-size: clamp(1.2rem, 3.1vw, 2.1rem);
  font-weight: 800;
  color: var(--clr-text-dark);
  line-height: 1.1;
}

.next-badge {
  background: #0b7c4b;
  color: #ffffff;
  font-size: clamp(0.65rem, 1.4vw, 0.95rem);
  font-weight: 800;
  padding: 0.2vh 0.9vw;
  border-radius: 999px;
  letter-spacing: 0.05em;
}

.meta-line {
  display: flex;
  align-items: center;
  gap: 0.8vw;
  font-size: clamp(0.8rem, 1.8vw, 1.25rem);
  color: #334155;
  font-weight: 600;
}

.meta-code {
  font-weight: 700;
  color: #0f172a;
}

.meta-sep {
  opacity: 0.5;
}

.meta-status {
  color: var(--clr-header);
  font-weight: 700;
}

.pickup-dial {
  --size: 4.6vh;
  flex-shrink: 0;
  font-size: clamp(0.85rem, 1.9vw, 1.3rem);
}

/* Bottom part of each pickup card: dual progress bars */
.pickup-bars {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2.5vw;
  width: 100%;
  margin-top: 0.4vh;
}

.prog-col {
  display: flex;
  flex-direction: column;
  gap: 0.35vh;
}

.prog-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-size: clamp(0.75rem, 1.7vw, 1.2rem);
  color: var(--clr-text-dark);
}

.prog-label {
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: #1e293b;
}

.prog-val {
  font-variant-numeric: tabular-nums;
  font-weight: 600;
  color: #334155;
}

.prog-val strong {
  font-weight: 800;
  color: #0f172a;
}

.prog-track {
  width: 100%;
  height: 1.35vh;
  min-height: 10px;
  background: #cbd5e1;
  border-radius: 999px;
  overflow: hidden;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.15);
}

.prog-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.4s ease;
}

.fill-pick {
  background: linear-gradient(90deg, #f59e0b 0%, #eab308 100%);
}

.fill-load {
  background: linear-gradient(90deg, #004580 0%, #0284c7 100%);
}
</style>
