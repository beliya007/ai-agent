<template>
  <div class="article-agent-layout">
    <el-card class="chat-area" shadow="always">
      <template #header>
        <div class="panel-title">聊天搜索区</div>
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
          placeholder="输入问题进行搜索，结果会流式返回"
          @keydown.enter.prevent="handleEnter"
        />
        <div class="actions">
          <el-button :disabled="isStreaming" @click="clearMessages">清空</el-button>
          <el-button type="primary" :loading="isStreaming" @click="sendMessage">发送</el-button>
        </div>
      </div>
    </el-card>

    <el-card class="preview-area" shadow="always">
      <template #header>
        <div class="panel-title">内容预览区</div>
      </template>

      <div v-if="latestAssistantReply" class="preview-content">{{ latestAssistantReply }}</div>
      <el-empty v-else description="右侧预览区域（可用于文章/报告/结构化结果展示）" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
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

const latestAssistantReply = computed(() => {
  for (let i = messages.value.length - 1; i >= 0; i -= 1) {
    const item = messages.value[i]
    if (item.role === 'assistant' && item.content.trim()) {
      return item.content
    }
  }
  return ''
})

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

  const ts = Date.now()
  const userMessageId = `user-${ts}`
  const assistantMessageId = `assistant-${ts}`

  messages.value.push({ id: userMessageId, role: 'user', content })
  messages.value.push({ id: assistantMessageId, role: 'assistant', content: '' })

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
    ElMessage.error(error.message || '流式搜索失败，请稍后重试')
  } finally {
    isStreaming.value = false
  }
}
</script>

<style scoped>
.article-agent-layout {
  max-width: 1400px;
  margin: 0 auto;
  padding: 10px 20px 20px;
  display: grid;
  gap: 16px;
  grid-template-columns: minmax(360px, 1fr) minmax(380px, 1fr);
}

.chat-area,
.preview-area {
  border-radius: 18px;
}

.panel-title {
  font-size: 16px;
  font-weight: 700;
  color: #1f2937;
}

.message-container {
  height: calc(100vh - 290px);
  min-height: 360px;
  overflow-y: auto;
  padding: 6px 4px 8px;
}

.message-row {
  display: flex;
  margin-bottom: 10px;
}

.message-row.is-user {
  justify-content: flex-end;
}

.message-row.is-assistant {
  justify-content: flex-start;
}

.bubble {
  max-width: 88%;
  white-space: pre-wrap;
  line-height: 1.6;
  padding: 10px 12px;
  border-radius: 12px;
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
  margin-top: 8px;
  padding-top: 10px;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 10px;
}

.preview-content {
  height: calc(100vh - 290px);
  min-height: 360px;
  overflow-y: auto;
  white-space: pre-wrap;
  line-height: 1.7;
  color: #1f2937;
  padding-right: 4px;
}

@media (max-width: 1024px) {
  .article-agent-layout {
    grid-template-columns: 1fr;
  }

  .message-container,
  .preview-content {
    height: 420px;
  }
}
</style>
