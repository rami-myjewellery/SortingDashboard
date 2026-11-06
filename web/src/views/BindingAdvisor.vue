<!-- src/views/BindingAdvisor.vue -->
<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import axios from 'axios'

interface BindingRow {
  carton_type: string
  pick_batch_priority_code: string | number
  no_of_cartons: number
  no_of_full_carts: number
  oldest_creation_datetime: string
}

const CLOUD_API =
  'https://sorting-dashboard-api-208732756826.europe-west4.run.app/dashboard/BindingAdvisor'
const LOCAL_API = 'http://127.0.0.1:5001/dashboard/BindingAdvisor'

const DEFAULT_ROWS: BindingRow[] = [
  {
    carton_type: 'PDL',
    pick_batch_priority_code: '5',
    no_of_cartons: 10,
    no_of_full_carts: 1.1,
    oldest_creation_datetime: '2026-11-03 09:06:23.000'
  },
  {
    carton_type: 'PDS',
    pick_batch_priority_code: '2',
    no_of_cartons: 2,
    no_of_full_carts: 0.1,
    oldest_creation_datetime: '2026-11-02 20:27:29.000'
  },
  {
    carton_type: 'BKL',
    pick_batch_priority_code: '5',
    no_of_cartons: 5,
    no_of_full_carts: 0.1,
    oldest_creation_datetime: '2026-11-03 06:39:05.000'
  },
  {
    carton_type: 'PDM',
    pick_batch_priority_code: '5',
    no_of_cartons: 4,
    no_of_full_carts: 0.4,
    oldest_creation_datetime: '2026-11-03 09:07:06.000'
  }
]

const rows = ref<BindingRow[]>(DEFAULT_ROWS)

function normalizeRows(incoming: any[]): BindingRow[] {
  return incoming.map((item) => ({
    carton_type: String(item.carton_type ?? item.CARTON_TYPE ?? '').trim(),
    pick_batch_priority_code: String(
      item.pick_batch_priority_code ?? item.PICK_BATCH_PRIORITY_CODE ?? ''
    ).trim(),
    no_of_cartons: Number(item.no_of_cartons ?? item.NO_OF_CARTONS ?? 0),
    no_of_full_carts: Number(item.no_of_full_carts ?? item.NO_OF_FULL_CARTS ?? 0),
    oldest_creation_datetime: String(
      item.oldest_creation_datetime ?? item.OLDEST_CREATION_DATETIME ?? '—'
    ).trim()
  }))
}

const advisedCartonType = computed<string>(() => {
  const top = rows.value[0]?.carton_type
  return top ? top.toUpperCase() : '—'
})

function formatFullCarts(val: number): string {
  if (!Number.isFinite(val)) return '0.0'
  return val.toFixed(1)
}

const fetchData = async () => {
  const isLocal =
    typeof window !== 'undefined' &&
    (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')

  const endpoints = isLocal ? [LOCAL_API, CLOUD_API] : [CLOUD_API]

  for (const url of endpoints) {
    try {
      const res = await axios.get(url)
      if (Array.isArray(res.data?.binding_rows)) {
        rows.value = normalizeRows(res.data.binding_rows)
        return
      }
    } catch {
      // try next endpoint or keep current/default rows
    }
  }
}

let hadNoBgClass = false

onMounted(() => {
  document.body.classList.remove('status-risk', 'status-bad')
  document.body.classList.add('status-good')
  hadNoBgClass = document.documentElement.classList.contains('no-bg')
  document.documentElement.classList.add('no-bg')

  fetchData()
  const id = setInterval(fetchData, 5_000)
  onBeforeUnmount(() => {
    clearInterval(id)
    if (!hadNoBgClass) {
      document.documentElement.classList.remove('no-bg')
    }
  })
})
</script>

<template>
  <div class="ba-viewport">
    <header class="ba-header">BINDING ADVISOR</header>

    <main class="ba-main">
      <!-- Top Hero Advice Card -->
      <section class="ba-hero-card">
        <div class="ba-hero-type">{{ advisedCartonType }}</div>

        <!-- Fast shipping carton icon with speed lines -->
        <div class="ba-hero-icon" aria-hidden="true">
          <svg viewBox="0 0 220 110" fill="none" xmlns="http://www.w3.org/2000/svg">
            <!-- Speed lines on the left -->
            <line
              x1="46"
              y1="34"
              x2="86"
              y2="34"
              stroke="white"
              stroke-width="6.5"
              stroke-linecap="round"
            />
            <line
              x1="20"
              y1="52"
              x2="86"
              y2="52"
              stroke="white"
              stroke-width="6.5"
              stroke-linecap="round"
            />
            <line
              x1="46"
              y1="70"
              x2="86"
              y2="70"
              stroke="white"
              stroke-width="6.5"
              stroke-linecap="round"
            />

            <!-- Isometric 3D Carton Box -->
            <!-- Top left flap -->
            <polygon points="145,14 102,32 123,41 166,23" fill="white" />
            <!-- Top right flap (with tape gap) -->
            <polygon points="173,26 130,44 145,51 188,32" fill="white" />
            <!-- Small tape tab on front-right edge -->
            <polygon points="154,34 166,39 166,52 154,47" fill="white" opacity="0.9" />
            <!-- Left vertical face -->
            <polygon points="100,37 142,55 142,98 100,79" fill="white" />
            <!-- Right vertical face -->
            <polygon points="148,55 190,37 190,79 148,98" fill="white" />
          </svg>
        </div>

        <p v-if="rows.length > 0" class="ba-hero-subtitle">
          WE ADVISE TO BIND AND PICK<br />
          <span>{{ advisedCartonType }} FIRST</span>
        </p>
        <p v-else class="ba-hero-subtitle">
          NO OPEN CARTONS TO BIND
        </p>
      </section>

      <!-- Priority Table Card -->
      <section class="ba-table-card">
        <div class="ba-table-scroll">
          <table class="ba-table">
            <thead>
              <tr>
                <th class="col-type">
                  <div class="th-inner">
                    <span>CARTON_TYPE</span>
                    <span class="th-caret">▼</span>
                  </div>
                </th>
                <th class="col-prio">
                  <div class="th-inner">
                    <span>PICK_BATCH_<br />PRIORITY_CODE</span>
                    <span class="th-caret">▼</span>
                  </div>
                </th>
                <th class="col-cartons">
                  <div class="th-inner">
                    <span>NO_OF_<br />CARTONS</span>
                    <span class="th-caret">▼</span>
                  </div>
                </th>
                <th class="col-carts">
                  <div class="th-inner">
                    <span>NO_OF_FULL<br />CARTS</span>
                    <span class="th-caret">▼</span>
                  </div>
                </th>
                <th class="col-oldest">
                  <div class="th-inner">
                    <span>OLDEST_CREATION_<br />DATETIME</span>
                    <span class="th-caret">▼</span>
                  </div>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in rows" :key="`${row.carton_type}-${row.pick_batch_priority_code}-${idx}`">
                <td class="cell-type">{{ row.carton_type }}</td>
                <td class="cell-prio">{{ row.pick_batch_priority_code }}</td>
                <td class="cell-cartons">{{ row.no_of_cartons }}</td>
                <td class="cell-carts">{{ formatFullCarts(row.no_of_full_carts) }}</td>
                <td class="cell-oldest">{{ row.oldest_creation_datetime }}</td>
              </tr>
              <tr v-if="rows.length === 0">
                <td colspan="5" class="cell-empty">Geen openstaande FMA dozen gevonden.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- Decorative bottom-right watermark carton -->
      <div class="ba-watermark" aria-hidden="true">
        <svg viewBox="0 0 360 280" fill="none" xmlns="http://www.w3.org/2000/svg">
          <!-- Speed lines -->
          <line
            x1="28"
            y1="148"
            x2="92"
            y2="148"
            stroke="currentColor"
            stroke-width="14"
            stroke-linecap="round"
          />
          <line
            x1="4"
            y1="186"
            x2="92"
            y2="186"
            stroke="currentColor"
            stroke-width="14"
            stroke-linecap="round"
          />
          <line
            x1="36"
            y1="224"
            x2="92"
            y2="224"
            stroke="currentColor"
            stroke-width="14"
            stroke-linecap="round"
          />

          <!-- Large isometric carton -->
          <polygon points="235,16 125,64 176,88 286,40" fill="currentColor" />
          <polygon points="302,47 192,95 235,115 345,67" fill="currentColor" />
          <polygon points="120,76 227,126 227,256 120,204" fill="currentColor" />
          <polygon points="243,126 350,76 350,204 243,256" fill="currentColor" />
        </svg>
      </div>
    </main>
  </div>
</template>

<style scoped>
.ba-viewport {
  display: flex;
  flex-direction: column;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background: #128842;
  position: relative;
}

.ba-header {
  flex: 0 0 auto;
  height: clamp(64px, 9.5vh, 115px);
  background: #044389;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: clamp(2.1rem, 5.4vw, 4.6rem);
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.2);
  z-index: 2;
}

.ba-main {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: clamp(14px, 2.4vh, 32px) clamp(14px, 2.8vw, 44px);
  gap: clamp(14px, 2.4vh, 28px);
  position: relative;
  z-index: 1;
  overflow-y: auto;
}

/* ── Top Hero Card ── */
.ba-hero-card {
  width: 100%;
  max-width: 1360px;
  background: rgba(255, 255, 255, 0.13);
  border-radius: clamp(16px, 2vw, 28px);
  padding: clamp(16px, 2.8vh, 36px) clamp(16px, 3vw, 40px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  box-sizing: border-box;
  z-index: 2;
}

.ba-hero-type {
  font-size: clamp(4.2rem, 12vw, 8.8rem);
  font-weight: 800;
  line-height: 0.98;
  letter-spacing: 0.02em;
  color: #ffffff;
  text-transform: uppercase;
}

.ba-hero-icon {
  width: clamp(130px, 22vw, 220px);
  height: clamp(64px, 10.5vh, 110px);
  margin: clamp(4px, 0.8vh, 12px) 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ba-hero-icon svg {
  width: 100%;
  height: 100%;
}

.ba-hero-subtitle {
  margin: clamp(4px, 0.6vh, 10px) 0 0;
  font-size: clamp(1.35rem, 3.3vw, 2.65rem);
  font-weight: 800;
  line-height: 1.18;
  letter-spacing: 0.03em;
  color: #ffffff;
  text-transform: uppercase;
}

/* ── Table Card ── */
.ba-table-card {
  width: 100%;
  max-width: 1360px;
  background: #ffffff;
  border-radius: clamp(16px, 2vw, 26px);
  padding: clamp(10px, 1.6vw, 22px);
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.2);
  box-sizing: border-box;
  z-index: 2;
}

.ba-table-scroll {
  width: 100%;
  overflow-x: auto;
}

.ba-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: auto;
  color: #0e2a47;
}

.ba-table thead th {
  background: #0b4f9c;
  color: #ffffff;
  font-size: clamp(0.76rem, 1.55vw, 1.25rem);
  font-weight: 700;
  text-align: left;
  padding: clamp(10px, 1.4vh, 18px) clamp(8px, 1.2vw, 16px);
  border-right: 1px solid rgba(255, 255, 255, 0.35);
  vertical-align: middle;
  line-height: 1.2;
}

.ba-table thead th:last-child {
  border-right: none;
}

.th-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.th-caret {
  font-size: 0.8em;
  opacity: 0.95;
  flex-shrink: 0;
}

.ba-table tbody tr:nth-child(odd) {
  background: #d7e8fa;
}

.ba-table tbody tr:nth-child(even) {
  background: #ffffff;
}

.ba-table tbody td {
  padding: clamp(10px, 1.6vh, 20px) clamp(8px, 1.2vw, 18px);
  border-right: 1px solid #c5dbf2;
  border-bottom: 1px solid #c5dbf2;
  color: #0d2b49;
  vertical-align: middle;
}

.ba-table tbody td:last-child {
  border-right: none;
}

.ba-table tbody tr:last-child td {
  border-bottom: none;
}

.cell-type {
  font-size: clamp(1.35rem, 3.1vw, 2.35rem);
  font-weight: 800;
  text-align: left;
  letter-spacing: 0.01em;
}

.cell-prio {
  font-size: clamp(1.1rem, 2.4vw, 1.85rem);
  font-weight: 700;
  text-align: left;
  font-variant-numeric: tabular-nums;
}

.cell-cartons,
.cell-carts {
  font-size: clamp(1.1rem, 2.4vw, 1.85rem);
  font-weight: 700;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.cell-oldest {
  font-size: clamp(0.88rem, 1.75vw, 1.38rem);
  font-weight: 700;
  text-align: left;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.cell-empty {
  text-align: center;
  font-size: clamp(1.1rem, 2.2vw, 1.6rem);
  font-weight: 600;
  color: #475569;
  padding: 2.5rem 1rem !important;
}

/* ── Decorative Watermark Carton in Bottom-Right ── */
.ba-watermark {
  position: fixed;
  right: clamp(12px, 3vw, 48px);
  bottom: clamp(-10px, 1vh, 24px);
  width: clamp(210px, 38vw, 420px);
  height: auto;
  color: rgba(255, 255, 255, 0.14);
  pointer-events: none;
  z-index: 0;
}

.ba-watermark svg {
  width: 100%;
  height: auto;
  display: block;
}
</style>
