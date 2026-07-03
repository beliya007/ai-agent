<template>
  <el-card class="chat-panel" shadow="always">
    <template #header>
      <div class="panel-header">
        <span class="panel-title">我的聊天Agent</span>
      </div>
    </template>

    <div ref="messageContainerRef" class="message-container">
      <div
        v-for="item in messages"
        :key="item.id"
        :class="['message-row', item.role === 'user' ? 'is-user' : 'is-assistant']"
      >
        <div class="bubble">{{ item.content }}</div>
      </div>
    </div>

    <div class="input-bar">
      <el-input
        v-model="inputMessage"
        type="textarea"
        :rows="3"
        maxlength="2000"
        show-word-limit
        placeholder="输入你的问题，聊天Agent会流式回复"
        @keydown.enter.prevent="handleEnter"
      />
      <div class="actions">
        <el-button :disabled="isStreaming" @click="clearMessages">清空</el-button>
        <el-button type="primary" :loading="isStreaming" @click="sendMessage">发送</el-button>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { nextTick, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { streamChat } from '@/services/api'

interface ChatMessageItem {
  id: string
  role: 'user' | 'assistant'
  content: string
}

const inputMessage = ref('')
const isStreaming = ref(false)
const messages = ref<ChatMessageItem[]>([])
const messageContainerRef = ref<HTMLElement | null>(null)

const scrollToBottom = async () => {
  await nextTick()
  if (messageContainerRef.value) {
    messageContainerRef.value.scrollTop = messageContainerRef.value.scrollHeight
  }
}

const clearMessages = () => {
  messages.value = []
}

const handleEnter = (event: KeyboardEvent) => {
  if (event.shiftKey) {
    return
  }
  sendMessage()
}

const sendMessage = async () => {
  const content = inputMessage.value.trim()
  if (!content || isStreaming.value) {
    return
  }

  const userMessageId = `user-${Date.now()}`
  const assistantMessageId = `assistant-${Date.now()}`

  messages.value.push({
    id: userMessageId,
    role: 'user',
    content,
  })

  messages.value.push({
    id: assistantMessageId,
    role: 'assistant',
    content: '',
  })

  inputMessage.value = ''
  isStreaming.value = true
  await scrollToBottom()

  try {
    await streamChat(content, {
      onChunk: async (chunk) => {
        const target = messages.value.find((item) => item.id === assistantMessageId)
        if (target) {
          target.content += chunk
          await scrollToBottom()
        }
      },
      onError: (message) => {
        ElMessage.error(message)
      },
    })
  } catch (error: any) {
    ElMessage.error(error.message || '聊天失败，请稍后重试')
  } finally {
    isStreaming.value = false
  }
}
</script>

<style scoped>
.chat-panel {
  max-width: 1400px;
  margin: 0 auto;
  border-radius: 20px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.panel-title {
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
}

.message-container {
  height: calc(100vh - 280px);
  min-height: 360px;
  overflow-y: auto;
  padding: 12px 4px;
}

.message-row {
  display: flex;
  margin-bottom: 12px;
}

.message-row.is-user {
  justify-content: flex-end;
}

.message-row.is-assistant {
  justify-content: flex-start;
}

.bubble {
  max-width: min(70%, 780px);
  white-space: pre-wrap;
  line-height: 1.6;
  padding: 10px 14px;
  border-radius: 14px;
}

.is-user .bubble {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #fff;
}

.is-assistant .bubble {
  background: #f3f4f6;
  color: #111827;
}

.input-bar {
  border-top: 1px solid #e5e7eb;
  margin-top: 10px;
  padding-top: 12px;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 10px;
}
</style>
