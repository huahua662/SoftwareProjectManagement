<template>
  <div class="chat-viewer">
    <div v-if="records.length === 0" style="text-align:center;color:#909399;padding:40px">
      暂无聊天记录
    </div>
    <div v-for="r in records" :key="r.id" class="chat-msg" :class="{ 'is-right': isRight(r.sender) }">
      <div class="chat-sender">{{ r.sender || '未知' }}</div>
      <div class="chat-bubble-row">
        <div class="chat-bubble">
          <template v-if="r.msg_type === 'text'">{{ r.content }}</template>
          <template v-else-if="r.msg_type === 'image'">
            <img v-if="r.media_path" :src="mediaUrl(r.media_path)" style="max-width:200px;border-radius:8px" />
            <span v-else>[图片]</span>
            {{ r.transcription || '' }}
          </template>
          <template v-else-if="r.msg_type === 'voice'">[语音] {{ r.transcription || r.content }}</template>
          <template v-else-if="r.msg_type === 'video'">[视频] {{ r.transcription || r.content }}</template>
          <template v-else-if="r.msg_type === 'file'">
            <a v-if="r.media_path" :href="mediaUrl(r.media_path)" target="_blank" class="file-link">
              <el-icon><Document /></el-icon>
              {{ r.content || '文件' }}
            </a>
            <span v-else>[文件] {{ r.content }}</span>
          </template>
          <template v-else>{{ r.content }}</template>
        </div>
        <el-button
          v-if="deletable"
          class="chat-del-btn"
          :icon="Delete"
          size="small"
          text
          circle
          @click.stop="$emit('delete', r.id)"
        />
      </div>
      <div class="chat-time" v-if="r.timestamp">{{ r.timestamp }}</div>
    </div>
  </div>
</template>

<script setup>
import { Delete, Document } from '@element-plus/icons-vue'

defineProps({
  records: { type: Array, default: () => [] },
  deletable: { type: Boolean, default: false },
})
defineEmits(['delete'])

const senders = new Set()
function isRight(sender) {
  if (!sender) return false
  senders.add(sender)
  const arr = [...senders]
  return arr.indexOf(sender) % 2 === 1
}

function mediaUrl(path) {
  if (!path) return ''
  const normalized = path.replace(/\\/g, '/')
  return `http://localhost:8000/${normalized}`
}
</script>

<style scoped>
.chat-viewer {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.chat-msg {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  max-width: 85%;
}
.chat-msg.is-right {
  align-self: flex-end;
  align-items: flex-end;
}
.chat-sender {
  font-size: 12px;
  color: #909399;
  margin-bottom: 2px;
}
.chat-bubble-row {
  display: flex;
  align-items: center;
  gap: 6px;
}
.chat-del-btn {
  color: #c0c4cc !important;
  flex-shrink: 0;
}
.chat-del-btn:hover {
  color: #f56c6c !important;
}
.chat-bubble {
  background: #f0f2f5;
  padding: 8px 12px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
  word-break: break-all;
}
.chat-msg.is-right .chat-bubble {
  background: #ecf5ff;
  color: #303133;
}
.chat-time {
  font-size: 11px;
  color: #c0c4cc;
  margin-top: 2px;
}
.file-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #409eff;
  text-decoration: none;
  word-break: break-all;
}
.file-link:hover {
  text-decoration: underline;
}
</style>
