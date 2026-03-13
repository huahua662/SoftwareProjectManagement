<template>
  <div class="page-container">
    <div class="page-header">
      <div style="display:flex;align-items:center;gap:12px">
        <el-button text @click="$router.push(`/project/${id}`)"><el-icon><ArrowLeft /></el-icon></el-button>
        <h2>需求文档</h2>
      </div>
      <div style="display:flex;gap:8px">
        <el-button @click="showChat = !showChat">
          <el-icon><ChatDotRound /></el-icon>
          {{ showChat ? '隐藏聊天记录' : '显示聊天记录' }}
          <el-badge :value="chatRecords.length" :max="99" type="info" style="margin-left:6px" v-if="chatRecords.length" />
        </el-button>
        <el-button type="primary" @click="runAnalysis" :loading="analyzing" :disabled="streaming">
          <el-icon><MagicStick /></el-icon> AI 分析
        </el-button>
      </div>
    </div>

    <!-- Streaming progress -->
    <el-card v-if="streaming" style="margin-bottom:16px">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
        <el-icon class="is-loading" :size="18" color="#409eff"><Loading /></el-icon>
        <span style="font-weight:600">{{ streamStage }}</span>
      </div>
      <el-progress :percentage="streamProgress" :stroke-width="10" :text-inside="true" style="margin-bottom:12px" />
      <div v-if="streamContent" class="markdown-content stream-preview" v-html="streamRendered" />
    </el-card>

    <el-row :gutter="16">
      <!-- Chat records panel -->
      <el-col :span="showChat ? 8 : 0" v-show="showChat">
        <el-card class="chat-panel">
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span>聊天记录 ({{ chatRecords.length }})</span>
              <el-button size="small" text @click="$router.push(`/project/${id}/import`)">
                <el-icon><Plus /></el-icon> 导入更多
              </el-button>
            </div>
          </template>
          <ChatViewer :records="chatRecords" :deletable="true" @delete="deleteRecord" style="max-height:calc(100vh - 260px);overflow-y:auto" />
        </el-card>
      </el-col>

      <!-- Requirement doc -->
      <el-col :span="showChat ? (editing ? 8 : 16) : (editing ? 12 : 24)">
        <el-card v-if="requirement">
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span>{{ requirement.title }} (v{{ requirement.version }})</span>
              <div>
                <el-dropdown trigger="click" @command="handleDownload" style="margin-right:8px">
                  <el-button size="small">
                    <el-icon><Download /></el-icon> 下载
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="md">Markdown (.md)</el-dropdown-item>
                      <el-dropdown-item command="html">HTML (.html)</el-dropdown-item>
                      <el-dropdown-item command="txt">纯文本 (.txt)</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
                <el-button size="small" @click="editing = !editing">{{ editing ? '取消编辑' : '编辑' }}</el-button>
                <el-button size="small" type="success" v-if="editing" @click="saveRequirement">保存</el-button>
              </div>
            </div>
          </template>
          <div v-if="!editing" class="markdown-content" v-html="renderedContent" />
        </el-card>
        <el-empty v-else-if="!streaming" description="暂无需求文档，请先导入聊天记录后点击 AI 分析" />
      </el-col>

      <!-- Edit panel -->
      <el-col :span="showChat ? 8 : 12" v-if="editing">
        <el-card>
          <template #header><span>编辑</span></template>
          <el-input v-model="editTitle" placeholder="标题" style="margin-bottom:12px" />
          <el-input v-model="editContent" type="textarea" :rows="25" placeholder="Markdown 内容" />
        </el-card>
      </el-col>
    </el-row>

    <el-card v-if="requirements.length > 1" style="margin-top:20px">
      <template #header><span>历史版本</span></template>
      <el-timeline>
        <el-timeline-item v-for="r in requirements" :key="r.id" :timestamp="r.created_at">
          <el-link @click="switchVersion(r)">{{ r.title }} (v{{ r.version }})</el-link>
        </el-timeline-item>
      </el-timeline>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'
import { Loading } from '@element-plus/icons-vue'
import api from '../api'
import ChatViewer from '../components/ChatViewer.vue'

const route = useRoute()
const id = computed(() => route.params.id)

const requirements = ref([])
const requirement = ref(null)
const editing = ref(false)
const editTitle = ref('')
const editContent = ref('')
const analyzing = ref(false)
const showChat = ref(true)
const chatRecords = ref([])

// Streaming state
const streaming = ref(false)
const streamStage = ref('')
const streamProgress = ref(0)
const streamContent = ref('')
const streamRendered = computed(() => streamContent.value ? marked(streamContent.value) : '')

const renderedContent = computed(() => {
  if (!requirement.value?.content) return ''
  return marked(requirement.value.content)
})

onMounted(async () => {
  await Promise.all([loadRequirements(), loadChatRecords()])
})

async function loadChatRecords() {
  try {
    const { data } = await api.get(`/chat/${id.value}/records`)
    chatRecords.value = data
  } catch {}
}

async function deleteRecord(recordId) {
  try {
    await api.delete(`/chat/record/${recordId}`)
    chatRecords.value = chatRecords.value.filter(r => r.id !== recordId)
  } catch {
    ElMessage.error('删除失败')
  }
}

async function loadRequirements() {
  try {
    const { data } = await api.get(`/analysis/requirements/${id.value}`)
    requirements.value = data
    if (data.length > 0) {
      requirement.value = data[0]
      editTitle.value = data[0].title
      editContent.value = data[0].content
    }
  } catch {}
}

function switchVersion(r) {
  requirement.value = r
  editTitle.value = r.title
  editContent.value = r.content
}

async function runAnalysis() {
  analyzing.value = true
  streaming.value = true
  streamStage.value = '正在分析聊天记录...'
  streamProgress.value = 10
  streamContent.value = ''

  try {
    const baseUrl = api.defaults.baseURL
    const url = `${baseUrl}/analysis/analyze/stream?project_id=${id.value}`
    const response = await fetch(url, { method: 'POST' })

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(err.detail || '分析失败')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const payload = line.slice(6).trim()
        if (payload === '[DONE]') continue

        try {
          const evt = JSON.parse(payload)
          if (evt.stage) streamStage.value = evt.stage
          if (evt.progress !== undefined) streamProgress.value = evt.progress
          if (evt.chunk) streamContent.value += evt.chunk
          if (evt.content) streamContent.value = evt.content
          if (evt.task_count !== undefined) {
            ElMessage.success(`分析完成，生成 ${evt.task_count} 个任务`)
          }
          if (evt.error) throw new Error(evt.error)
        } catch (e) {
          if (e.message && !e.message.includes('JSON')) throw e
        }
      }
    }

    await loadRequirements()
  } catch (e) {
    ElMessage.error('分析失败: ' + e.message)
  } finally {
    analyzing.value = false
    streaming.value = false
    streamProgress.value = 100
  }
}

function handleDownload(format) {
  if (!requirement.value) return
  const title = requirement.value.title || '需求文档'
  const content = requirement.value.content || ''
  let blob, ext
  if (format === 'md') {
    blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
    ext = 'md'
  } else if (format === 'html') {
    const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>${title}</title><style>body{font-family:system-ui,sans-serif;max-width:900px;margin:40px auto;padding:0 20px;line-height:1.8;color:#333}h1,h2,h3{color:#1a1a1a}code{background:#f4f4f5;padding:2px 6px;border-radius:4px}pre{background:#f4f4f5;padding:16px;border-radius:8px;overflow-x:auto}table{border-collapse:collapse;width:100%}th,td{border:1px solid #ddd;padding:8px 12px;text-align:left}</style></head><body>${marked(content)}</body></html>`
    blob = new Blob([html], { type: 'text/html;charset=utf-8' })
    ext = 'html'
  } else {
    const plain = content.replace(/#{1,6}\s/g, '').replace(/\*{1,2}(.*?)\*{1,2}/g, '$1').replace(/`{1,3}[^`]*`{1,3}/g, m => m.replace(/`/g, ''))
    blob = new Blob([plain], { type: 'text/plain;charset=utf-8' })
    ext = 'txt'
  }
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${title}_v${requirement.value.version}.${ext}`
  a.click()
  URL.revokeObjectURL(url)
}

async function saveRequirement() {
  if (!requirement.value) return
  try {
    const { data } = await api.put(`/analysis/requirements/${requirement.value.id}`, {
      title: editTitle.value,
      content: editContent.value,
    })
    requirement.value = { ...requirement.value, ...data }
    editing.value = false
    ElMessage.success('已保存')
  } catch {
    ElMessage.error('保存失败')
  }
}
</script>

<style scoped>
.chat-panel :deep(.el-card__body) {
  padding: 12px;
}
.stream-preview {
  max-height: 300px;
  overflow-y: auto;
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #ebeef5;
}
</style>
