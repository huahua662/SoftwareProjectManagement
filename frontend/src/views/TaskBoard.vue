<template>
  <div class="page-container">
    <div class="page-header">
      <div style="display:flex;align-items:center;gap:12px">
        <el-button text @click="$router.push(`/project/${id}`)"><el-icon><ArrowLeft /></el-icon></el-button>
        <h2>任务看板</h2>
      </div>
      <div style="display:flex;gap:8px">
        <el-button @click="showAdd = true"><el-icon><Plus /></el-icon> 添加任务</el-button>
        <el-button type="success" @click="batchGenerate" :loading="generating">
          <el-icon><MagicStick /></el-icon> 批量生成代码
        </el-button>
        <el-button type="warning" @click="exportProject" :loading="exporting">
          <el-icon><Download /></el-icon> 导出项目
        </el-button>
      </div>
    </div>

    <el-row :gutter="16" v-loading="taskStore.loading">
      <el-col :span="6" v-for="col in columns" :key="col.status">
        <div class="board-column">
          <div class="board-column-header" :style="{ borderColor: col.color }">
            <span>{{ col.label }}</span>
            <el-badge :value="getColumnTasks(col.status).length" type="info" />
          </div>
          <div class="board-column-body">
            <TaskItem
              v-for="task in getColumnTasks(col.status)"
              :key="task.id"
              :task="task"
              @status-change="(s) => changeStatus(task.id, s)"
              @generate="() => generateSingle(task.id)"
              @view-code="() => viewCode(task)"
              @delete="() => handleDelete(task.id)"
            />
            <el-empty v-if="getColumnTasks(col.status).length === 0" description="暂无任务" :image-size="60" />
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- Add task dialog -->
    <el-dialog v-model="showAdd" title="添加任务" width="500px">
      <el-form :model="addForm" label-width="80px">
        <el-form-item label="任务标题"><el-input v-model="addForm.title" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="addForm.description" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="优先级">
          <el-radio-group v-model="addForm.priority">
            <el-radio value="高">高</el-radio>
            <el-radio value="中">中</el-radio>
            <el-radio value="低">低</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="预估工时">
          <el-input-number v-model="addForm.estimated_hours" :min="0.5" :step="0.5" />
          <span style="margin-left:8px">小时</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAdd = false">取消</el-button>
        <el-button type="primary" @click="handleAdd">添加</el-button>
      </template>
    </el-dialog>

    <!-- Code viewer dialog -->
    <el-dialog v-model="showCode" title="代码预览" width="70%">
      <pre class="code-preview"><code>{{ codeContent }}</code></pre>
      <template #footer>
        <span style="color:#909399;margin-right:auto">{{ codePath }}</span>
        <el-button @click="showCode = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useTaskStore } from '../stores/task'
import TaskItem from '../components/TaskItem.vue'
import api from '../api'

const route = useRoute()
const taskStore = useTaskStore()
const id = computed(() => route.params.id)

const columns = [
  { status: '待开发', label: '待开发', color: '#909399' },
  { status: '开发中', label: '开发中', color: '#e6a23c' },
  { status: 'AI生成中', label: 'AI生成中', color: '#409eff' },
  { status: '已完成', label: '已完成', color: '#67c23a' },
]

const showAdd = ref(false)
const addForm = ref({ title: '', description: '', priority: '中', estimated_hours: 4 })
const generating = ref(false)
const exporting = ref(false)
const showCode = ref(false)
const codeContent = ref('')
const codePath = ref('')

onMounted(() => taskStore.fetchTasks(id.value))

function getColumnTasks(status) {
  return taskStore.tasks.filter(t => t.status === status)
}

async function changeStatus(taskId, newStatus) {
  await taskStore.updateTask(taskId, { status: newStatus })
}

async function handleAdd() {
  if (!addForm.value.title.trim()) {
    ElMessage.warning('请输入任务标题')
    return
  }
  await taskStore.createTask({ ...addForm.value, project_id: parseInt(id.value) })
  showAdd.value = false
  addForm.value = { title: '', description: '', priority: '中', estimated_hours: 4 }
  ElMessage.success('已添加')
}

async function handleDelete(taskId) {
  try {
    await ElMessageBox.confirm('确定删除此任务？', '提示', { type: 'warning' })
    await taskStore.deleteTask(taskId)
    ElMessage.success('已删除')
  } catch {}
}

async function generateSingle(taskId) {
  try {
    const { data } = await api.post('/codegen/generate', { task_id: taskId })
    ElMessage.success('代码生成完成')
    await taskStore.fetchTasks(id.value)
  } catch (e) {
    ElMessage.error('生成失败: ' + (e.response?.data?.detail || e.message))
  }
}

async function batchGenerate() {
  generating.value = true
  try {
    const { data } = await api.post('/codegen/generate/batch', { project_id: parseInt(id.value) })
    ElMessage.success(data.detail)
    await taskStore.fetchTasks(id.value)
  } catch (e) {
    ElMessage.error('批量生成失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    generating.value = false
  }
}

async function exportProject() {
  exporting.value = true
  try {
    const response = await api.post(`/codegen/export/${id.value}`, {}, { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `project_${id.value}.zip`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

function viewCode(task) {
  codeContent.value = task.code_content || '暂无代码'
  codePath.value = task.code_path || ''
  showCode.value = true
}
</script>

<style scoped>
.board-column {
  background: #f0f2f5;
  border-radius: 8px;
  min-height: 500px;
}
.board-column-header {
  padding: 12px 16px;
  font-weight: 600;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 3px solid;
  border-radius: 8px 8px 0 0;
  background: #fff;
}
.board-column-body {
  padding: 8px;
}
.code-preview {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  max-height: 500px;
  font-family: 'Fira Code', monospace;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
}
</style>
