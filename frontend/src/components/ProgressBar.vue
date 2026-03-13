<template>
  <div class="progress-bar-wrapper">
    <div class="progress-bar-bg">
      <div class="progress-bar-fill" :style="{ width: percentage + '%', backgroundColor: color }" />
    </div>
    <span class="progress-text">{{ percentage.toFixed(1) }}%</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  percentage: { type: Number, default: 0 },
})

const color = computed(() => {
  if (props.percentage >= 100) return '#67c23a'
  if (props.percentage >= 60) return '#409eff'
  if (props.percentage >= 30) return '#e6a23c'
  return '#909399'
})
</script>

<style scoped>
.progress-bar-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  max-width: 150px;
}
.progress-bar-bg {
  flex: 1;
  height: 6px;
  background: #e4e7ed;
  border-radius: 3px;
  overflow: hidden;
}
.progress-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}
.progress-text {
  font-size: 12px;
  color: #909399;
  min-width: 42px;
  text-align: right;
}
</style>
