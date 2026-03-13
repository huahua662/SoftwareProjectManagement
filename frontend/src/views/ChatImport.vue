<template>
  <div class="page-container">
    <div class="page-header">
      <div style="display:flex;align-items:center;gap:12px">
        <el-button text @click="$router.push(`/project/${id}`)"><el-icon><ArrowLeft /></el-icon></el-button>
        <h2>导入聊天记录</h2>
      </div>
    </div>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header><span>导入聊天记录</span></template>
          <el-tabs v-model="activeTab">
            <!-- WeChat clipboard import - primary -->
            <el-tab-pane label="微信导入" name="wechat">
              <div class="step-guide">
                <div class="step">
                  <div class="step-num">1</div>
                  <div class="step-text">打开微信聊天窗口，<b>长按</b>任意一条消息</div>
                </div>
                <div class="step">
                  <div class="step-num">2</div>
                  <div class="step-text">点击 <b>"多选"</b>，勾选需要的消息</div>
                </div>
                <div class="step">
                  <div class="step-num">3</div>
                  <div class="step-text">
                    点击底部 <b>"合并转发"</b> 发给自己（文件传输助手），<br/>
                    然后打开合并消息 → 全选复制<br/>
                    <span style="color:#909399;font-size:12px">或直接多选后右键"复制"（如果有的话）</span>
                  </div>
                </div>
                <div class="step">
                  <div class="step-num">4</div>
                  <div class="step-text">点击下方按钮，自动从剪贴板读取</div>
                </div>
              </div>

              <el-button
                type="primary"
                size="large"
                style="width:100%;margin-top:16px"
                @click="readClipboard"
                :loading="importing"
              >
                <el-icon><DocumentCopy /></el-icon>
                从剪贴板导入
              </el-button>

              <el-divider>或者直接粘贴 / 拖拽</el-divider>

              <div
                class="chat-input-box"
                :class="{ 'is-dragover': isDragover }"
                @dragover.prevent="isDragover = true"
                @dragleave.prevent="isDragover = false"
                @drop.prevent="handleDrop"
              >
                <div v-if="inputAttachments.length" class="chat-input-attachments">
                  <div v-for="(att, idx) in inputAttachments" :key="idx" class="chat-input-att-item">
                    <el-image v-if="att.type === 'image'" :src="att.preview" fit="cover" class="att-thumb" />
                    <div v-else class="att-file-icon">
                      <el-icon :size="20"><Document /></el-icon>
                      <span class="att-file-name">{{ att.name }}</span>
                    </div>
                    <el-button class="att-remove" :icon="Close" size="small" circle text @click="removeAttachment(idx)" />
                  </div>
                </div>
                <div
                  ref="inputBoxRef"
                  class="chat-input-editable"
                  contenteditable="true"
                  :data-placeholder="inputPlaceholder"
                  @paste="handleInputPaste"
                  @keydown.enter.exact="handleInputEnter"
                ></div>
                <div class="chat-input-toolbar">
                  <label class="toolbar-btn">
                    <el-icon :size="18"><Picture /></el-icon>
                    <input type="file" accept="image/*" multiple hidden @change="handleToolbarFile($event, 'image')" />
                  </label>
                  <label class="toolbar-btn">
                    <el-icon :size="18"><FolderOpened /></el-icon>
                    <input type="file" multiple hidden @change="handleToolbarFile($event, 'file')" />
                  </label>
                  <div style="flex:1" />
                  <el-button type="primary" :loading="importing" :disabled="!hasInput" @click="handleUnifiedImport">
                    导入
                  </el-button>
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane label="截图识别" name="ocr">
              <div style="margin-bottom:12px;color:#606266;font-size:14px">
                上传聊天截图，AI 自动识别图中的聊天内容并导入
              </div>
              <el-upload
                drag
                :auto-upload="false"
                :on-change="handleOcrFile"
                :show-file-list="false"
                accept="image/*"
                multiple
              >
                <el-icon style="font-size:40px;color:#c0c4cc"><Picture /></el-icon>
                <div>拖拽或点击上传聊天截图</div>
                <template #tip>
                  <div class="el-upload__tip">支持 JPG / PNG / BMP / WebP 格式</div>
                </template>
              </el-upload>
              <div v-if="ocrPreviews.length" style="margin-top:12px">
                <div v-for="(p, idx) in ocrPreviews" :key="idx" style="margin-bottom:8px">
                  <el-image :src="p" style="max-height:120px;border-radius:8px" fit="contain" />
                </div>
              </div>
              <el-button
                v-if="ocrFiles.length"
                type="primary"
                style="width:100%;margin-top:12px"
                @click="submitOcr"
                :loading="ocrLoading"
              >
                <el-icon><MagicStick /></el-icon>
                识别并导入 ({{ ocrFiles.length }} 张)
              </el-button>
            </el-tab-pane>

            <el-tab-pane label="文件上传" name="file">
              <el-upload
                drag
                :auto-upload="false"
                :on-change="handleAnyFile"
                :show-file-list="false"
                multiple
              >
                <el-icon style="font-size:40px;color:#c0c4cc"><UploadFilled /></el-icon>
                <div>拖拽或点击上传文件</div>
                <template #tip>
                  <div class="el-upload__tip">
                    支持：JSON / CSV / TXT（聊天记录导入）<br/>
                    图片 / 视频 / 压缩包 / 其他文件（作为附件关联到项目）
                  </div>
                </template>
              </el-upload>
            </el-tab-pane>
          </el-tabs>
          <div v-if="uploadStatus" style="margin-top:12px">
            <el-alert :title="uploadStatus" :type="uploadOk ? 'success' : 'error'" show-icon :closable="true" />
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span>聊天记录预览 ({{ records.length }} 条)</span>
              <el-button size="small" type="danger" text @click="clearRecords" v-if="records.length">清空</el-button>
            </div>
          </template>
          <div v-if="records.length" style="margin-bottom:12px">
            <el-alert type="success" :closable="false">
              <template #title>
                已导入 {{ records.length }} 条记录，可前往
                <el-link type="primary" @click="$router.push(`/project/${id}/requirement`)">需求文档</el-link>
                页面进行 AI 分析
              </template>
            </el-alert>
          </div>
          <ChatViewer :records="records" :deletable="true" @delete="deleteRecord" style="max-height:460px;overflow-y:auto" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api'
import ChatViewer from '../components/ChatViewer.vue'

const route = useRoute()
const id = computed(() => route.params.id)

const activeTab = ref('wechat')
const records = ref([])
const uploadStatus = ref('')
const uploadOk = ref(false)
const pasteText = ref('')
const importing = ref(false)
const ocrFiles = ref([])
const ocrPreviews = ref([])
const ocrLoading = ref(false)

const inputBoxRef = ref(null)
const inputAttachments = ref([])
const isDragover = ref(false)
const inputPlaceholder = '粘贴文字、截图，或拖拽文件到这里... (Enter 发送)'
const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
const hasInput = computed(() => {
  return inputAttachments.value.length > 0 || (inputBoxRef.value && inputBoxRef.value.innerText.trim().length > 0)
})

onMounted(() => loadRecords())

async function loadRecords() {
  try {
    const { data } = await api.get(`/chat/${id.value}/records`)
    records.value = data
  } catch {}
}

async function deleteRecord(recordId) {
  try {
    await api.delete(`/chat/record/${recordId}`)
    records.value = records.value.filter(r => r.id !== recordId)
  } catch {
    ElMessage.error('删除失败')
  }
}

async function readClipboard() {
  try {
    const text = await navigator.clipboard.readText()
    if (!text || !text.trim()) {
      ElMessage.warning('剪贴板是空的，请先在微信中复制聊天内容')
      return
    }
    importing.value = true
    const { data } = await api.post(`/chat/${id.value}/import/paste`, { text })
    uploadStatus.value = data.detail
    uploadOk.value = true
    ElMessage.success(data.detail)
    await loadRecords()
  } catch (e) {
    if (e.name === 'NotAllowedError') {
      ElMessage.error('浏览器拒绝读取剪贴板，请允许剪贴板权限，或手动粘贴到下方文本框')
      return
    }
    uploadStatus.value = '导入失败: ' + (e.response?.data?.detail || e.message)
    uploadOk.value = false
    ElMessage.error('导入失败')
  } finally {
    importing.value = false
  }
}

async function handlePaste() {
  if (!pasteText.value.trim()) return
  importing.value = true
  try {
    const { data } = await api.post(`/chat/${id.value}/import/paste`, { text: pasteText.value })
    uploadStatus.value = data.detail
    uploadOk.value = true
    ElMessage.success(data.detail)
    pasteText.value = ''
    await loadRecords()
  } catch (e) {
    uploadStatus.value = '导入失败: ' + (e.response?.data?.detail || e.message)
    uploadOk.value = false
    ElMessage.error('导入失败')
  } finally {
    importing.value = false
  }
}

function addAttachment(file) {
  const name = file.name || 'file'
  const ext = name.split('.').pop().toLowerCase()
  const isImage = imageExts.includes(ext) || file.type.startsWith('image/')
  const att = { file, name, type: isImage ? 'image' : 'file', preview: '' }
  if (isImage) att.preview = URL.createObjectURL(file)
  inputAttachments.value.push(att)
}

function removeAttachment(idx) {
  const att = inputAttachments.value[idx]
  if (att.preview) URL.revokeObjectURL(att.preview)
  inputAttachments.value.splice(idx, 1)
}

function handleInputPaste(e) {
  const items = e.clipboardData?.items
  if (!items) return
  let hasFile = false
  for (const item of items) {
    if (item.kind === 'file') {
      hasFile = true
      const file = item.getAsFile()
      if (file) addAttachment(file)
    }
  }
  if (hasFile) {
    e.preventDefault()
  }
}

function handleDrop(e) {
  isDragover.value = false
  const files = e.dataTransfer?.files
  if (!files) return
  for (const file of files) {
    addAttachment(file)
  }
}

function handleToolbarFile(e, type) {
  const files = e.target.files
  if (!files) return
  for (const file of files) {
    addAttachment(file)
  }
  e.target.value = ''
}

function handleInputEnter(e) {
  if (e.isComposing) return
  e.preventDefault()
  handleUnifiedImport()
}

async function handleUnifiedImport() {
  const text = inputBoxRef.value ? inputBoxRef.value.innerText.trim() : ''
  const attachments = [...inputAttachments.value]
  if (!text && !attachments.length) return

  importing.value = true
  try {
    if (text) {
      const { data } = await api.post(`/chat/${id.value}/import/paste`, { text })
      ElMessage.success(data.detail)
    }

    for (const att of attachments) {
      const name = att.name
      const ext = name.split('.').pop().toLowerCase()
      const textTypes = { json: 'json', csv: 'csv', txt: 'txt' }

      if (textTypes[ext]) {
        const formData = new FormData()
        formData.append('file', att.file)
        const { data } = await api.post(`/chat/${id.value}/import/${textTypes[ext]}`, formData)
        ElMessage.success(data.detail)
      } else if (att.type === 'image') {
        const formData = new FormData()
        formData.append('file', att.file)
        formData.append('sender', '')
        formData.append('msg_type', 'image')
        await api.post(`/chat/${id.value}/upload/media`, formData)
        ElMessage.success(`已上传图片: ${name}`)
      } else {
        const formData = new FormData()
        formData.append('file', att.file)
        formData.append('sender', '')
        formData.append('msg_type', 'file')
        await api.post(`/chat/${id.value}/upload/media`, formData)
        ElMessage.success(`已上传: ${name}`)
      }
    }

    uploadStatus.value = '导入成功'
    uploadOk.value = true
    if (inputBoxRef.value) inputBoxRef.value.innerText = ''
    inputAttachments.value = []
    await loadRecords()
  } catch (e) {
    uploadStatus.value = '导入失败: ' + (e.response?.data?.detail || e.message)
    uploadOk.value = false
    ElMessage.error('导入失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    importing.value = false
  }
}

async function handleAnyFile(file) {
  const name = file.name || ''
  const ext = name.split('.').pop().toLowerCase()
  const textTypes = { json: 'json', csv: 'csv', txt: 'txt' }

  if (textTypes[ext]) {
    // Chat record file - use existing import endpoints
    const formData = new FormData()
    formData.append('file', file.raw)
    try {
      const { data } = await api.post(`/chat/${id.value}/import/${textTypes[ext]}`, formData)
      uploadStatus.value = data.detail
      uploadOk.value = true
      ElMessage.success(data.detail)
      await loadRecords()
    } catch (e) {
      uploadStatus.value = '导入失败: ' + (e.response?.data?.detail || e.message)
      uploadOk.value = false
      ElMessage.error('导入失败')
    }
  } else {
    // Media / other file - upload as attachment
    const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
    const videoExts = ['mp4', 'avi', 'mov', 'mkv', 'webm']
    let msgType = 'file'
    if (imageExts.includes(ext)) msgType = 'image'
    else if (videoExts.includes(ext)) msgType = 'video'

    const formData = new FormData()
    formData.append('file', file.raw)
    formData.append('sender', '')
    formData.append('msg_type', msgType)
    try {
      await api.post(`/chat/${id.value}/upload/media`, formData)
      uploadStatus.value = `已上传文件: ${name}`
      uploadOk.value = true
      ElMessage.success(`已上传: ${name}`)
      await loadRecords()
    } catch (e) {
      uploadStatus.value = '上传失败: ' + (e.response?.data?.detail || e.message)
      uploadOk.value = false
      ElMessage.error('上传失败')
    }
  }
}

function handleOcrFile(file) {
  ocrFiles.value.push(file.raw)
  const url = URL.createObjectURL(file.raw)
  ocrPreviews.value.push(url)
}

async function submitOcr() {
  if (!ocrFiles.value.length) return
  ocrLoading.value = true
  let totalCount = 0
  try {
    for (const file of ocrFiles.value) {
      const formData = new FormData()
      formData.append('file', file)
      const { data } = await api.post(`/chat/${id.value}/import/ocr`, formData, { timeout: 180000 })
      totalCount += data.count || 0
    }
    uploadStatus.value = `截图识别完成，共导入 ${totalCount} 条记录`
    uploadOk.value = true
    ElMessage.success(`截图识别完成，共导入 ${totalCount} 条记录`)
    ocrFiles.value = []
    ocrPreviews.value = []
    await loadRecords()
  } catch (e) {
    uploadStatus.value = '识别失败: ' + (e.response?.data?.detail || e.message)
    uploadOk.value = false
    ElMessage.error('截图识别失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    ocrLoading.value = false
  }
}

async function clearRecords() {
  try {
    await api.delete(`/chat/${id.value}/records`)
    records.value = []
    ElMessage.success('已清空')
  } catch {}
}
</script>

<style scoped>
.step-guide {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.step {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}
.step-num {
  width: 28px;
  height: 28px;
  min-width: 28px;
  border-radius: 50%;
  background: #409eff;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
}
.step-text {
  font-size: 14px;
  line-height: 1.6;
  color: #303133;
  padding-top: 3px;
}

.chat-input-box {
  border: 1px solid #dcdfe6;
  border-radius: 12px;
  background: #fff;
  transition: border-color 0.2s, box-shadow 0.2s;
  overflow: hidden;
}
.chat-input-box:focus-within {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.15);
}
.chat-input-box.is-dragover {
  border-color: #67c23a;
  background: #f0f9eb;
}

.chat-input-attachments {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 10px 12px 0;
}
.chat-input-att-item {
  position: relative;
}
.att-thumb {
  width: 64px;
  height: 64px;
  border-radius: 6px;
  border: 1px solid #ebeef5;
}
.att-file-icon {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  background: #f4f4f5;
  border-radius: 6px;
  font-size: 12px;
  color: #606266;
  max-width: 150px;
}
.att-file-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.att-remove {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 18px !important;
  height: 18px !important;
  background: #f56c6c !important;
  color: #fff !important;
  font-size: 10px;
  border: none !important;
}

.chat-input-editable {
  min-height: 80px;
  max-height: 200px;
  overflow-y: auto;
  padding: 10px 12px;
  font-size: 14px;
  line-height: 1.6;
  outline: none;
  color: #303133;
  word-break: break-all;
}
.chat-input-editable:empty::before {
  content: attr(data-placeholder);
  color: #c0c4cc;
  pointer-events: none;
}

.chat-input-toolbar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border-top: 1px solid #f0f0f0;
}
.toolbar-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  cursor: pointer;
  color: #909399;
  transition: background 0.2s, color 0.2s;
}
.toolbar-btn:hover {
  background: #f4f4f5;
  color: #409eff;
}
</style>
