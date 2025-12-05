<script setup>
import { computed } from 'vue'

const props = defineProps({
  person:        { type: Object, required: true },
  action:        { type: Object, required: true },
  idleThreshold: { type: Number, default: 40 }, // seconds
  showIdleTimer: { type: Boolean, default: true }
})

// safe access
const idleSeconds = computed(() =>
    Math.max(0, Number(props.person?.idleSeconds ?? 0))
)

// simple class based on inactivity only
const perfClass = computed(() => {
  return idleSeconds.value > props.idleThreshold ? 'idle' : 'good'
})

// format like "1h 2m 3s", "12m 4s", or "15s"
const idleDisplay = computed(() => {
  let s = idleSeconds.value
  const h = Math.floor(s / 3600); s %= 3600
  const m = Math.floor(s / 60);   s = Math.floor(s % 60)
  const parts = []
  if (h) parts.push(`${h}h`)
  if (m) parts.push(`${m}m`)
  parts.push(`${s}s`)
  return parts.join(' ')
})
</script>

<template>
  <div class="person-bar" :class="perfClass">
    <span class="person-name">{{ person.name }}</span>
    <div class="person-action" style="font-size: medium; text-align: right">
      {{ person.action }}
    </div>

    <div class="details" v-if="showIdleTimer">
      <div class="clock" :title="`${idleSeconds}s inactive`"></div>
      <div class="idle-badge">
        Inactive: <strong>{{ idleDisplay }}</strong>
      </div>
    </div>
  </div>
</template>

<!-- styles are global in your setup; example helpers if you want:
.idle-badge { padding: 2px 8px; border-radius: 9999px; font-variant-numeric: tabular-nums; }
.person-bar.idle .idle-badge { background: #fff2f2; }
.person-bar.good .idle-badge { background: #f4fff2; }
-->
