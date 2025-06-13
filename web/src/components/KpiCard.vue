<script setup>
defineProps({label: String, value: Number, unit: String})
</script>

<template>
  <div class="kpi-card">
    <div class="kpi-value">{{ value }}</div>
    <div class="kpi-title">{{ unit }}</div>
    <div class="kpi-label">{{ label }}</div>
  </div>
</template>

<style scoped>
.kpi-card {
  background: rgba(255, 255, 255, 0.18);
  padding: 2vh;
  border-radius: 12px;
  text-align: center;
  min-width: 26vw;
  z-index: 2;
}

.kpi-value {
  font-size: 15vw;
  font-weight: 700;
  line-height: 1;
}

.kpi-title {
  font-size: 6vw;
  font-weight: 700;
  line-height: 1;
}

.kpi-label {
  font-size: 2.5vw;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-top: 0.8vh;
}
</style>
