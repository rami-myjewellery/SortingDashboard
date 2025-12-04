<script setup lang="ts">
import { computed,ref, onMounted  } from 'vue'
import { useRoute } from 'vue-router'

import KpiCard   from './KpiCard.vue'
import PersonBar from './PersonBar.vue'

/* ───────── props ───────── */
interface Kpi { label: string; value: number }
interface Person {
  name: string
  last_seen?: string | number | Date
  lastSeen?: string | number | Date
  idleSeconds?: number
  [key: string]: unknown
}

const props = defineProps<{
  data: {
    title: string
    historyText?: string
    idleThreshold?: number
    kpis: Kpi[]
    people: Person[]
  }
}>()

/* ───────── route helpers ───────── */
const route      = useRoute()
const mode       = computed(() => route.params.mode as string | undefined)
/* start with a default – must match the server’s HTML */
const showPeople = ref(false)
const showIdleTimer = ref(true)
const visiblePeople = computed(() => {
  const list = Array.isArray(props.data.people) ? [...props.data.people] : []
  const now = Date.now()
  return list
      .map((person) => {
        const rawLastSeen = person.last_seen ?? person.lastSeen
        const parsed = rawLastSeen ? new Date(rawLastSeen).getTime() : NaN
        const fallback = typeof person.idleSeconds === 'number' ? now - person.idleSeconds * 1000 : 0
        const ts = Number.isFinite(parsed) ? parsed : fallback
        return { ts, person }
      })
      .sort((a, b) => b.ts - a.ts)
      .slice(0, 10)
      .map((entry) => entry.person)
})

/* run only in the browser */
onMounted(() => {
  const params = new URLSearchParams(window.location.search)
  showPeople.value = params.get('bool') === 'true'
  showIdleTimer.value = params.get('timer') !== 'false'
})
</script>

<template>
  <header>{{ props.data.title }}</header>

  <main>
    <section class="kpi-area">
      <div class="kpis">
        <KpiCard
            v-for="(k, idx) in props.data.kpis"
            :key="k.label"
            v-bind="k"
            :class="{ 'wide-kpi': idx === 2 && props.data.kpis.length > 2 }"
        />
      </div>
    </section>
    

    <p class="history">{{ props.data.historyText }}</p>
    <ClientOnly>
    <section class="people-list" v-if="showPeople">
      <PersonBar
          v-for="p in visiblePeople"
          :key="p.name"
          :person="p"
          :idle-threshold="props.data.idleThreshold ?? 40"
          :show-idle-timer="showIdleTimer"
      />
    </section>
    </ClientOnly>
  </main>
</template>
