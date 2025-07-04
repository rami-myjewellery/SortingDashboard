<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import KpiCard   from './KpiCard.vue'
import PersonBar from './PersonBar.vue'

/* ───────── props ───────── */
interface Kpi { label: string; value: number }
interface Person { name: string; /* … */ }

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
const showPeople = computed(() => route.query.bool === 'true')
const mode       = computed(() => route.params.mode as string | undefined)
</script>

<template>
  <header>{{ props.data.title }}</header>

  <main>
    <section class="kpi-area">
      <div class="kpis">
        <KpiCard
            v-for="k in props.data.kpis"
            :key="k.label"
            v-bind="k"
        />
      </div>
    </section>

    <p class="history">{{ props.data.historyText }}</p>

    <section class="people-list" v-if="showPeople">
      <PersonBar
          v-for="p in props.data.people"
          :key="p.name"
          :person="p"
          :idle-threshold="props.data.idleThreshold ?? 40"
      />
    </section>
  </main>
</template>
