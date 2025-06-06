<script setup>
import KpiCard   from './KpiCard.vue'
import PersonBar from './PersonBar.vue'
import { useRoute } from 'vue-router'
import { computed } from 'vue'

const route = useRoute()

// Computed to reactively track query changes
const showPeople = computed(() => route.query.bool === 'true')
defineProps({ data: Object })
</script>

<template>
  <header>{{ data.title }}</header>

  <main>
    <section class="kpi-area">
      <div class="kpis">
        <KpiCard v-for="k in data.kpis" :key="k.label" v-bind="k" />
      </div>
    </section>

    <p class="history">{{ data.historyText }}</p>

    <section class="people-list" v-if="showPeople">
      <PersonBar
          v-for="p in data.people"
          :key="p.name"
          :person="p"
          :idle-threshold="data.idleThreshold ?? 40"
      />
    </section>
  </main>
</template>
