<script setup lang="ts">
import { computed,ref, onMounted  } from 'vue'
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
const mode       = computed(() => route.params.mode as string | undefined)
/* start with a default – must match the server’s HTML */
const showPeople = ref(false)
const showIdleTimer = ref(true)

/* run only in the browser */
onMounted(() => {
  showPeople.value =
      new URLSearchParams(window.location.search).get('bool') === 'true'
  showIdleTimer.value =
      new URLSearchParams(window.location.search).get('timer') !== 'false'
})
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
    <ClientOnly>
    <section class="people-list" v-if="showPeople">
      <PersonBar
          v-for="p in props.data.people"
          :key="p.name"
          :person="p"
          :idle-threshold="props.data.idleThreshold ?? 40"
          :show-idle-timer="showIdleTimer"
      />
    </section>
    </ClientOnly>
  </main>
</template>
