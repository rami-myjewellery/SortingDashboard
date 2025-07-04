<script setup>
import { computed } from 'vue'

const props = defineProps({
  person:        { type: Object, required: true },
  action:        { type: Object, required: true },
  idleThreshold: { type: Number, default: 40 }
})

const perfClass = computed(() => {
  if (props.person.idleSeconds > props.idleThreshold) return 'idle'
  if (props.person.speed >= 75) return 'good'
  if (props.person.speed >= 50) return 'warn'
  return 'bad'
})
</script>

<template>
  <div class="person-bar" :class="perfClass">
    <span class="name">{{ person.name }}</span>
    <div style="font-size: medium; text-align: right" class="name">{{ person.action }}</div>

    <div class="details">
      <div class="clock" :title="`${person.idleSeconds}s`"></div>
      <div
          class="dial"
          :class="perfClass"
          :style="{ '--value': person.speed }"
      >
        <span>{{ person.speed }}%</span>
      </div>
    </div>
  </div>
</template>

<!-- GEEN scoped styles nodig: alles staat globaal -->
