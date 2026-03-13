<template>
  <el-card shadow="hover" class="project-card" @click="$emit('click')">
    <div class="project-card-header">
      <h3>{{ project.name }}</h3>
      <div @click.stop>
        <el-dropdown trigger="click" @command="onCommand">
          <el-button text size="small"><el-icon><MoreFilled /></el-icon></el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="delete">
                <el-icon><Delete /></el-icon> 删除
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
    <p class="project-desc">{{ project.description || '暂无描述' }}</p>
    <div class="project-footer">
      <el-tag size="small" :type="statusType">{{ project.status }}</el-tag>
      <span v-if="project.budget" class="project-budget">¥{{ project.budget.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</span>
      <ProgressBar :percentage="project.progress" />
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'
import ProgressBar from './ProgressBar.vue'

const props = defineProps({
  project: { type: Object, required: true },
})
const emit = defineEmits(['click', 'delete'])

function onCommand(cmd) {
  if (cmd === 'delete') emit('delete')
}

const statusType = computed(() => {
  const s = props.project.status
  if (s === '已完成') return 'success'
  if (s === '开发中') return 'warning'
  if (s === '已归档') return 'info'
  return ''
})
</script>

<style scoped>
.project-card {
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}
.project-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
}
.project-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.project-card-header h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}
.project-desc {
  color: #909399;
  font-size: 13px;
  margin-bottom: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.project-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}
.project-budget {
  font-size: 13px;
  font-weight: 600;
  color: #f56c6c;
}
</style>
