<!-- src/views/NextDayProgress.vue -->
<script setup lang="ts">
import { ref, computed, watchEffect, onMounted, onBeforeUnmount } from 'vue'
import axios from 'axios'
import { useRoute } from 'vue-router'
import KpiCard from '@/components/KpiCard.vue'

interface DockLoad {
  id: string
  load_date?: string
  load_code: string
  load_designation: string
  carrier?: string
  dock: string
  planned_loading_time?: string
  scheduled_time: string
  picks_confirmed: number
  picks_done?: number
  picks_total: number
  pick_pct: number
  picks_percentage?: number
}

const API = 'https://sorting-dashboard-api-208732756826.europe-west4.run.app/dashboard/NextDayProgress'
const ALLOWED_LOAD_CODES = new Set(['PNLMAI', 'PNLPAR', 'DHLFY'])

// ── Default Dataset matching the Reflex DBeaver query (PNLMAI, PNLPAR, DHLFY) ──
const DEFAULT_LOADS: DockLoad[] = [
  {
    id: 'load-pnlmai',
    load_code: 'PNLMAI',
    load_designation: 'PostNL Brievenbuspakje',
    dock: 'DOCK002',
    planned_loading_time: '223000',
    scheduled_time: '22:30',
    picks_confirmed: 412,
    picks_total: 460,
    pick_pct: 90
  },
  {
    id: 'load-pnlpar',
    load_code: 'PNLPAR',
    load_designation: 'PostNL Pakketten',
    dock: 'DOCK003',
    planned_loading_time: '230000',
    scheduled_time: '23:00',
    picks_confirmed: 582,
    picks_total: 970,
    pick_pct: 60
  },
  {
    id: 'load-dhlfy',
    load_code: 'DHLFY',
    load_designation: 'DHL For You',
    dock: 'DOCK005',
    planned_loading_time: '233000',
    scheduled_time: '23:30',
    picks_confirmed: 145,
    picks_total: 520,
    pick_pct: 28
  }
]

const route = useRoute()

// Thresholds from specification:
// Groen > 85%, Oranje 50%-85%, Rood < 50% (overridable via ?green=98 if needed)
const greenThreshold = computed(() => {
  const q = Number(route.query.green)
  return Number.isFinite(q) && q > 0 ? q : 85
})
const orangeThreshold = computed(() => {
  const q = Number(route.query.orange)
  return Number.isFinite(q) && q > 0 ? q : 50
})

const rawLoads = ref<DockLoad[]>(DEFAULT_LOADS)

function formatHhmmssToHhmm(raw?: string | number): string {
  if (!raw) return '00:00'
  const s = String(raw).trim()
  if (s.includes(':')) return s.slice(0, 5)
  const digits = s.replace(/\D/g, '').padStart(6, '0')
  return `${digits.slice(0, 2)}:${digits.slice(2, 4)}`
}

function normalizeIncomingLoads(incoming: any[]): DockLoad[] {
  const normalized = incoming
    .map((item, idx) => {
      const rawCode = String(item.load_code ?? '').trim()
      // Extract clean code if legacy mock had date prefix like "23/10/26 PNLPAR"
      const cleanCode = rawCode.split(/\s+/).pop() || rawCode
      const confirmed = Number(item.picks_confirmed ?? item.picks_done ?? 0)
      const total = Number(item.picks_total ?? 0)
      const pct =
        item.pick_pct !== undefined && item.pick_pct !== null
          ? Number(item.pick_pct)
          : item.picks_percentage !== undefined
          ? Math.round(Number(item.picks_percentage))
          : total > 0
          ? Math.round((confirmed / total) * 100)
          : 0

      return {
        id: item.id || `load-${cleanCode.toLowerCase()}-${idx}`,
        load_date: item.load_date,
        load_code: cleanCode,
        load_designation: String(item.load_designation || item.carrier || cleanCode).trim(),
        dock: String(item.dock || '—').trim(),
        planned_loading_time: String(item.planned_loading_time || ''),
        scheduled_time: item.scheduled_time
          ? String(item.scheduled_time).slice(0, 5)
          : formatHhmmssToHhmm(item.planned_loading_time),
        picks_confirmed: confirmed,
        picks_total: total,
        pick_pct: pct
      }
    })
    .filter((l) => ALLOWED_LOAD_CODES.has(l.load_code))

  return normalized.length > 0 ? normalized : DEFAULT_LOADS
}

// Chronological sort from earliest upcoming departure to latest (matching ORDER BY cghdch, cgccha)
const sortedLoads = computed<DockLoad[]>(() => {
  return [...rawLoads.value].sort((a, b) => {
    const normTime = (t: string) => {
      const [h, m] = t.split(':').map(Number)
      return h < 6 ? (h + 24) * 60 + m : h * 60 + m
    }
    const diff = normTime(a.scheduled_time) - normTime(b.scheduled_time)
    return diff !== 0 ? diff : a.load_code.localeCompare(b.load_code)
  })
})

// Earliest scheduled_time (can include 1, 2 or more simultaneous loads)
const earliestTime = computed(() => sortedLoads.value[0]?.scheduled_time ?? null)

const earliestLoads = computed(() => {
  if (!earliestTime.value) return []
  return sortedLoads.value.filter((l) => l.scheduled_time === earliestTime.value)
})

function isEarliestMoment(load: DockLoad) {
  return earliestTime.value !== null && load.scheduled_time === earliestTime.value
}

function dialClass(pct: number): 'good' | 'warn' | 'bad' {
  if (pct > greenThreshold.value) return 'good'
  if (pct >= orangeThreshold.value) return 'warn'
  return 'bad'
}

// Background status reflects the earliest pickup moment(s):
// Groen > 85%, Oranje 50%-85%, Rood < 50%
const computedStatus = computed<'good' | 'risk' | 'bad'>(() => {
  if (!earliestLoads.value.length) return 'good'
  const minPct = Math.min(...earliestLoads.value.map((l) => l.pick_pct))
  if (minPct > greenThreshold.value) return 'good'
  if (minPct >= orangeThreshold.value) return 'risk'
  return 'bad'
})

const topKpis = computed(() => {
  const confirmedPicks = sortedLoads.value.reduce((acc, l) => acc + l.picks_confirmed, 0)
  const totalPicks = sortedLoads.value.reduce((acc, l) => acc + l.picks_total, 0)
  const openPicks = Math.max(0, totalPicks - confirmedPicks)
  return [
    {
      label: 'Openstaande Picks',
      value: openPicks,
      unit: 'picks'
    },
    {
      label: 'Geconfirmde Picks',
      value: confirmedPicks,
      unit: 'picks'
    }
  ]
})

const historyText = computed(() => {
  if (!earliestLoads.value.length) return ''
  const first = earliestLoads.value[0]
  const designations = earliestLoads.value
    .map((l) => `${l.load_designation} (${l.dock})`)
    .join(' & ')
  return `Eerstvolgende load: ${first.scheduled_time} · ${designations}`
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
      // Only overwrite if the backend is returning the new 3-load dataset (with PNLMAI or load_designation)
      const hasNewFormat = res.data.loads.some(
        (l: any) => l.load_designation || l.load_code === 'PNLMAI'
      )
      if (hasNewFormat) {
        rawLoads.value = normalizeIncomingLoads(res.data.loads)
      }
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
</script>

<template>
  <header>Next Day Progress</header>

  <main class="nd-main">
    <!-- Top KPI section: 2 side-by-side KpiCards (Openstaande Picks & Geconfirmde Picks) -->
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

    <!-- Chronological load rows from top (earliest) to bottom: PNLMAI, PNLPAR, DHLFY -->
    <section class="people-list pickup-list">
      <div
        v-for="load in sortedLoads"
        :key="load.id"
        class="person-bar pickup-card"
        :class="[
          { 'is-next': isEarliestMoment(load) },
          `card-${dialClass(load.pick_pct)}`
        ]"
      >
        <!-- Top row of card: Planned Loading Time + Dock + Load Designation + Dial -->
        <div class="pickup-top">
          <div class="pickup-left">
            <div
              class="time-badge"
              :class="isEarliestMoment(load) ? `badge-${dialClass(load.pick_pct)}` : ''"
            >
              <span class="time-main">{{ load.scheduled_time }}</span>
              <span class="time-dock">{{ load.dock }}</span>
            </div>

            <div class="carrier-block">
              <div class="carrier-line">
                <span class="carrier-title">{{ load.load_designation }}</span>
                <span
                  v-if="isEarliestMoment(load)"
                  class="next-badge"
                  :class="`badge-${dialClass(load.pick_pct)}`"
                >
                  EERSTVOLGEND
                </span>
              </div>
              <div class="meta-line">
                <span class="meta-code">{{ load.load_code }}</span>
                <span class="meta-sep">•</span>
                <span>Geplande laadtijd: {{ load.scheduled_time }}</span>
                <span class="meta-sep">•</span>
                <span class="meta-status">Dock: {{ load.dock }}</span>
              </div>
            </div>
          </div>

          <div
            class="dial pickup-dial"
            :class="dialClass(load.pick_pct)"
            :style="{ '--value': Math.round(load.pick_pct) }"
          >
            <span>{{ Math.round(load.pick_pct) }}%</span>
          </div>
        </div>

        <!-- Bottom row of card: Single full-width progress bar for Confirmed Picks -->
        <div class="pickup-bar-single">
          <div class="prog-head">
            <span class="prog-label">Geconfirmde Picks</span>
            <span class="prog-val">
              <strong>{{ load.picks_confirmed.toLocaleString('nl-NL') }}</strong> /
              {{ load.picks_total.toLocaleString('nl-NL') }} picks
              ({{ Math.round(load.pick_pct) }}%)
            </span>
          </div>
          <div class="prog-track">
            <div
              class="prog-fill"
              :class="`fill-${dialClass(load.pick_pct)}`"
              :style="{ width: `${Math.min(100, Math.max(0, load.pick_pct))}%` }"
            ></div>
          </div>
        </div>
      </div>
    </section>
  </main>
</template>

<style scoped>
.nd-main {
  padding: 2vh 2.5vw 3vh 2.5vw;
}

.nd-kpi-area {
  flex: 0 0 22vh;
}

.nd-kpi-area :deep(.kpi-card) {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 1.5vh 1.5vw;
}

.nd-kpi-area :deep(.kpi-value) {
  font-size: clamp(3rem, 11vw, 6.2rem);
}

.nd-kpi-area :deep(.kpi-title) {
  font-size: clamp(1.4rem, 4.2vw, 2.6rem);
}

.nd-kpi-area :deep(.kpi-label) {
  font-size: clamp(0.95rem, 2.2vw, 1.5rem);
}

.nd-history {
  margin: 1.4vh 0 1.2vh 0;
  font-size: clamp(1.05rem, 2.3vw, 1.65rem);
  font-weight: 600;
}

.pickup-list {
  --person-gap: 2.2vh;
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  gap: var(--person-gap);
  margin-top: 0.8vh;
}

.pickup-card {
  height: auto !important;
  min-height: 14.5vh;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: stretch;
  padding: 2vh 2.5vw;
  background: rgba(232, 240, 250, 0.95);
  border-radius: 0 1rem 0 0;
  border-left: 1.2vw solid var(--clr-header);
  box-shadow: 0 5px 16px rgba(0, 0, 0, 0.18);
  box-sizing: border-box;
}

.pickup-card.is-next {
  background: #ffffff;
  box-shadow: 0 8px 22px rgba(0, 0, 0, 0.28);
}

.pickup-card.is-next.card-good {
  border-left: 1.4vw solid #0b7c4b;
}

.pickup-card.is-next.card-warn {
  border-left: 1.4vw solid #ff9c2a;
}

.pickup-card.is-next.card-bad {
  border-left: 1.4vw solid #d6252c;
}

/* Top part of each pickup card */
.pickup-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 2vw;
}

.pickup-left {
  display: flex;
  align-items: center;
  gap: 2.2vw;
  min-width: 0;
}

.time-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--clr-header);
  color: #ffffff;
  border-radius: 0.6rem;
  padding: 0.7vh 1.6vw;
  min-width: 14vw;
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
  font-size: clamp(1.6rem, 4.2vw, 2.9rem);
  font-weight: 800;
  line-height: 1.05;
}

.time-dock {
  font-size: clamp(0.85rem, 1.8vw, 1.25rem);
  font-weight: 700;
  letter-spacing: 0.04em;
  opacity: 0.92;
  margin-top: 0.2vh;
}

.carrier-block {
  display: flex;
  flex-direction: column;
  gap: 0.4vh;
  min-width: 0;
}

.carrier-line {
  display: flex;
  align-items: center;
  gap: 1.4vw;
  flex-wrap: wrap;
}

.carrier-title {
  font-size: clamp(1.5rem, 3.8vw, 2.6rem);
  font-weight: 800;
  color: var(--clr-text-dark);
  line-height: 1.1;
}

.next-badge {
  background: #0b7c4b;
  color: #ffffff;
  font-size: clamp(0.75rem, 1.6vw, 1.1rem);
  font-weight: 800;
  padding: 0.25vh 1vw;
  border-radius: 999px;
  letter-spacing: 0.05em;
}

.meta-line {
  display: flex;
  align-items: center;
  gap: 0.9vw;
  font-size: clamp(0.95rem, 2.1vw, 1.45rem);
  color: #334155;
  font-weight: 600;
}

.meta-code {
  font-weight: 800;
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
  --size: 6vh;
  flex-shrink: 0;
  font-size: clamp(1.05rem, 2.4vw, 1.65rem);
}

/* Bottom part of each pickup card: single full-width progress bar */
.pickup-bar-single {
  display: flex;
  flex-direction: column;
  gap: 0.5vh;
  width: 100%;
  margin-top: 0.6vh;
}

.prog-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-size: clamp(0.95rem, 2.1vw, 1.45rem);
  color: var(--clr-text-dark);
}

.prog-label {
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.04em;
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
  height: 1.9vh;
  min-height: 14px;
  background: #cbd5e1;
  border-radius: 999px;
  overflow: hidden;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.18);
}

.prog-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.4s ease;
}

.fill-good {
  background: linear-gradient(90deg, #0b7c4b 0%, #13c38b 100%);
}

.fill-warn {
  background: linear-gradient(90deg, #d97706 0%, #ff9c2a 100%);
}

.fill-bad {
  background: linear-gradient(90deg, #b91c1c 0%, #d6252c 100%);
}
</style>
