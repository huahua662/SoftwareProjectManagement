<template>
  <div class="page-container">
    <div class="page-header">
      <div style="display:flex;align-items:center;gap:12px">
        <el-button text @click="$router.push('/')"><el-icon><ArrowLeft /></el-icon></el-button>
        <h2>{{ project?.name || '项目详情' }}</h2>
        <el-tag :type="statusType">{{ project?.status }}</el-tag>
      </div>
    </div>

    <el-row :gutter="16" style="margin-bottom:20px">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ project?.progress?.toFixed(1) || 0 }}%</div>
          <div class="stat-label">整体进度</div>
          <el-progress :percentage="project?.progress || 0" :show-text="false" :stroke-width="8" style="margin-top:8px" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card clickable" @click="$router.push(`/project/${id}/import`)">
          <div class="stat-value"><el-icon><ChatDotRound /></el-icon></div>
          <div class="stat-label">导入聊天记录</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card clickable" @click="$router.push(`/project/${id}/requirement`)">
          <div class="stat-value"><el-icon><Document /></el-icon></div>
          <div class="stat-label">需求文档</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card clickable" @click="$router.push(`/project/${id}/tasks`)">
          <div class="stat-value"><el-icon><List /></el-icon></div>
          <div class="stat-label">任务看板</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>项目信息</span>
          <el-button size="small" @click="openEdit" v-if="!editVisible">
            <el-icon><Edit /></el-icon> 编辑
          </el-button>
        </div>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="项目名称">{{ project?.name }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ project?.status }}</el-descriptions-item>
        <el-descriptions-item label="项目金额">¥{{ (project?.budget || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ project?.created_at }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ project?.description || '暂无描述' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-dialog v-model="editVisible" title="编辑项目信息" width="480px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="项目名称">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="editForm.status" style="width:100%">
            <el-option label="需求分析中" value="需求分析中" />
            <el-option label="开发中" value="开发中" />
            <el-option label="已完成" value="已完成" />
            <el-option label="已归档" value="已归档" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目金额">
          <el-input-number v-model="editForm.budget" :min="0" :precision="2" :step="1000" style="width:100%" controls-position="right" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" :rows="4" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useProjectStore } from '../stores/project'

const route = useRoute()
const store = useProjectStore()
const id = computed(() => route.params.id)
const project = computed(() => store.currentProject)

const editVisible = ref(false)
const saving = ref(false)
const editForm = ref({ name: '', description: '', status: '', budget: 0 })

const statusType = computed(() => {
  const s = project.value?.status
  if (s === '已完成') return 'success'
  if (s === '开发中') return 'warning'
  return 'info'
})

onMounted(() => store.fetchProject(id.value))

function openEdit() {
  editForm.value = {
    name: project.value?.name || '',
    description: project.value?.description || '',
    status: project.value?.status || '需求分析中',
    budget: project.value?.budget || 0,
  }
  editVisible.value = true
}

async function saveEdit() {
  if (!editForm.value.name.trim()) {
    ElMessage.warning('项目名称不能为空')
    return
  }
  saving.value = true
  try {
    await store.updateProject(Number(id.value), editForm.value)
    editVisible.value = false
    ElMessage.success('项目信息已更新')
  } catch (e) {
    ElMessage.error('保存失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.stat-card {
  text-align: center;
  cursor: default;
}
.stat-card.clickable {
  cursor: pointer;
  transition: transform 0.2s;
}
.stat-card.clickable:hover {
  transform: translateY(-2px);
}
.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #409eff;
}
.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}
</style>
