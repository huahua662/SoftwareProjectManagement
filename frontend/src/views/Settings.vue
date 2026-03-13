<template>
  <div class="page-container">
    <div class="page-header">
      <h2>系统设置</h2>
    </div>

    <el-card style="max-width:600px">
      <template #header><span>AI API 配置</span></template>
      <el-form :model="form" label-width="120px">
        <el-form-item label="API Base URL">
          <el-input v-model="form.ai_base_url" placeholder="https://api.openai.com/v1" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="form.ai_api_key" type="password" show-password placeholder="sk-..." />
        </el-form-item>
        <el-form-item label="模型名称">
          <el-input v-model="form.ai_model" placeholder="gpt-4o" />
        </el-form-item>
        <el-form-item label="视觉模型">
          <el-input v-model="form.ai_vision_model" placeholder="截图OCR专用，如 gpt-4o（留空则使用上方模型）" />
        </el-form-item>
        <el-form-item label="PyWxDump 路径">
          <el-input v-model="form.pywxdump_path" placeholder="可选，PyWxDump安装路径" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveSettings" :loading="saving">保存设置</el-button>
          <el-button @click="testAI" :loading="testing">测试 AI 连接</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const form = ref({
  ai_base_url: '',
  ai_api_key: '',
  ai_model: '',
  ai_vision_model: '',
  pywxdump_path: '',
})
const saving = ref(false)
const testing = ref(false)

onMounted(async () => {
  try {
    const { data } = await api.get('/settings')
    form.value = data
  } catch {
    ElMessage.error('无法加载设置，请检查后端服务')
  }
})

async function saveSettings() {
  saving.value = true
  try {
    const { data } = await api.put('/settings', form.value)
    ElMessage.success(data.detail)
    const { data: fresh } = await api.get('/settings')
    form.value = fresh
  } catch (e) {
    ElMessage.error('保存失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

async function testAI() {
  testing.value = true
  try {
    const { data } = await api.post('/settings/test-ai')
    if (data.ok) {
      ElMessage.success(data.detail)
    } else {
      ElMessage.error(data.detail)
    }
  } catch (e) {
    ElMessage.error('测试失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    testing.value = false
  }
}
</script>
