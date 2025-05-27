<script setup>
import KpiCard   from './KpiCard.vue'
import PersonBar from './PersonBar.vue'

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

    <section class="people-list">
      <PersonBar
          v-for="p in data.people"
          :key="p.name"
          :person="p"
          :idle-threshold="data.idleThreshold ?? 40"
      />
    </section>
  </main>
</template>
