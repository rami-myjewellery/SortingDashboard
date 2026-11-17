<!-- src/views/GeekPicking.vue -->
<script setup lang="ts">
import GeekNextDayLooper from '@/components/GeekNextDayLooper.vue'

const API = 'https://sorting-dashboard-api-208732756826.europe-west4.run.app/dashboard/GeekPicking'
</script>

<template>
  <!-- phaseOffset=1: :00–:29 NextDayProgress, :30–:59 GeekPicking -->
  <GeekNextDayLooper :api="API" :phase-offset="1" />
</template>
