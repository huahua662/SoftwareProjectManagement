<template>
  <div class="page-container">
    <div class="page-header">
      <h2>项目总览</h2>
      <el-button type="primary" @click="showCreate = true">
        <el-icon><Plus /></el-icon> 新建项目
      </el-button>
    </div>

    <el-card style="margin-bottom:20px">
      <div style="display:flex;align-items:center;gap:24px">
        <div>
          <div style="font-size:14px;color:#909399">项目总数</div>
          <div style="font-size:24px;font-weight:700;color:#303133">{{ store.projects.length }}</div>
        </div>
        <el-divider direction="vertical" style="height:40px" />
        <div>
          <div style="font-size:14px;color:#909399">金额总计</div>
          <div style="font-size:24px;font-weight:700;color:#f56c6c">¥{{ totalBudget }}</div>
        </div>
      </div>
    </el-card>

    <div v-loading="store.loading" class="card-grid">
      <ProjectCard
        v-for="p in store.projects"
        :key="p.id"
        :project="p"
        @click="goProject(p.id)"
        @delete="handleDelete(p.id)"
      />
      <el-empty v-if="!store.loading && store.projects.length === 0" description="暂无项目，点击右上角创建" />
    </div>

    <el-dialog v-model="showCreate" title="新建项目" width="480px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="项目名称">
          <el-input v-model="form.name" placeholder="输入项目名称" />
        </el-form-item>
        <el-form-item label="项目描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="简要描述项目" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="creating">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '../stores/project'
import { ElMessageBox, ElMessage } from 'element-plus'
import ProjectCard from '../components/ProjectCard.vue'

const store = useProjectStore()
const router = useRouter()

const showCreate = ref(false)
const creating = ref(false)
const form = ref({ name: '', description: '' })

const totalBudget = computed(() => {
  const sum = store.projects.reduce((s, p) => s + (p.budget || 0), 0)
  return sum.toLocaleString('zh-CN', { minimumFractionDigits: 2 })
})

onMounted(() => store.fetchProjects())

function goProject(id) {
  router.push(`/project/${id}`)
}

async function handleCreate() {
  if (!form.value.name.trim()) {
    ElMessage.warning('请输入项目名称')
    return
  }
  creating.value = true
  try {
    const p = await store.createProject(form.value)
    showCreate.value = false
    form.value = { name: '', description: '' }
    ElMessage.success('创建成功')
    router.push(`/project/${p.id}`)
  } catch (e) {
    ElMessage.error('创建失败')
  } finally {
    creating.value = false
  }
}

async function handleDelete(id) {
  try {
    await ElMessageBox.confirm('确定删除该项目？所有关联数据将被清除。', '提示', { type: 'warning' })
    await store.deleteProject(id)
    ElMessage.success('已删除')
  } catch {}
}
</script>
