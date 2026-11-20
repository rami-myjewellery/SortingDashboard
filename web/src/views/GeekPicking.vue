<!-- src/views/GeekPicking.vue -->
<script setup lang="ts">
import GeekNextDayLooper from '@/components/GeekNextDayLooper.vue'

const API = 'https://sorting-dashboard-api-208732756826.europe-west4.run.app/dashboard/GeekPicking'
</script>

<template>
  <!-- phaseOffset=0: :00–:29 GeekPicking, :30–:59 NextDayProgress (synced with GeekInbound) -->
  <GeekNextDayLooper :api="API" :phase-offset="0" />
</template>
