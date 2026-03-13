<template>
  <el-card shadow="hover" class="task-item" :class="`priority-${task.priority}`">
    <div class="task-header">
      <span class="task-title">{{ task.title }}</span>
      <el-dropdown trigger="click" size="small">
        <el-button text size="small"><el-icon><MoreFilled /></el-icon></el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item v-if="task.status !== '待开发'" @click="$emit('status-change', '待开发')">移至 待开发</el-dropdown-item>
            <el-dropdown-item v-if="task.status !== '开发中'" @click="$emit('status-change', '开发中')">移至 开发中</el-dropdown-item>
            <el-dropdown-item v-if="task.status !== '已完成'" @click="$emit('status-change', '已完成')">移至 已完成</el-dropdown-item>
            <el-dropdown-item divided v-if="task.status !== '已完成' && task.status !== 'AI生成中'" @click="$emit('generate')">
              <el-icon><MagicStick /></el-icon> AI 生成代码
            </el-dropdown-item>
            <el-dropdown-item v-if="task.code_content" @click="$emit('view-code')">
              <el-icon><View /></el-icon> 查看代码
            </el-dropdown-item>
            <el-dropdown-item divided @click="$emit('delete')" style="color:#f56c6c">
              <el-icon><Delete /></el-icon> 删除
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
    <p class="task-desc" v-if="task.description">{{ task.description }}</p>
    <div class="task-meta">
      <el-tag size="small" :type="priorityType" effect="plain">{{ task.priority }}</el-tag>
      <span v-if="task.estimated_hours" class="task-hours">{{ task.estimated_hours }}h</span>
      <el-icon v-if="task.code_content" style="color:#67c23a;margin-left:auto"><CircleCheckFilled /></el-icon>
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  task: { type: Object, required: true },
})
defineEmits(['status-change', 'generate', 'view-code', 'delete'])

const priorityType = computed(() => {
  if (props.task.priority === '高') return 'danger'
  if (props.task.priority === '低') return 'info'
  return 'warning'
})
</script>

<style scoped>
.task-item {
  margin-bottom: 8px;
  border-left: 3px solid transparent;
}
.task-item.priority-高 { border-left-color: #f56c6c; }
.task-item.priority-中 { border-left-color: #e6a23c; }
.task-item.priority-低 { border-left-color: #909399; }
.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}
.task-title {
  font-weight: 600;
  font-size: 14px;
  flex: 1;
}
.task-desc {
  font-size: 12px;
  color: #909399;
  margin: 6px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.task-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}
.task-hours {
  font-size: 12px;
  color: #909399;
}
</style>
