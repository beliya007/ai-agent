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

      <div class="preview-content">
        <div v-if="rewrittenQuery" class="meta-line">
          检索关键词: {{ rewrittenQuery }}
        </div>

        <div v-if="searchResults.length > 0" class="result-list">
          <div v-for="(item, index) in searchResults" :key="`${item.title}-${index}`" class="result-item">
            <a :href="item.url" target="_blank" rel="noopener noreferrer" class="result-title">{{ item.title }}</a>
            <p class="result-snippet">{{ item.snippet }}</p>
          </div>
        </div>

        <div v-if="latestAssistantReply" class="summary-block">{{ latestAssistantReply }}</div>

        <el-empty
          v-if="searchResults.length === 0 && !latestAssistantReply"
          description="输入问题后，右侧将展示搜索候选与汇总结果"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { streamArticleSearch } from '@/services/api'
import type { ArticleSearchItem } from '@/services/api'

interface ChatMessageItem {
  id: string
  role: 'user' | 'assistant'
  content: string
}

const inputMessage = ref('')
const isStreaming = ref(false)
const messages = ref<ChatMessageItem[]>([])
const rewrittenQuery = ref('')
const searchResults = ref<ArticleSearchItem[]>([])
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
  rewrittenQuery.value = ''
  searchResults.value = []
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
  rewrittenQuery.value = ''
  searchResults.value = []
  await scrollToBottom()

  try {
    await streamArticleSearch(content, {
      onSearchResults: (payload) => {
        rewrittenQuery.value = payload.rewritten_query
        searchResults.value = payload.articles
      },
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
  padding-right: 4px;
}

.meta-line {
  margin-bottom: 12px;
  padding: 8px 10px;
  border-radius: 10px;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 13px;
}

.result-list {
  display: grid;
  gap: 10px;
  margin-bottom: 12px;
}

.result-item {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 10px;
  background: #ffffff;
}

.result-title {
  color: #2563eb;
  font-weight: 600;
  text-decoration: none;
}

.result-title:hover {
  text-decoration: underline;
}

.result-snippet {
  margin: 8px 0 0;
  color: #4b5563;
  font-size: 13px;
  line-height: 1.6;
}

.summary-block {
  white-space: pre-wrap;
  line-height: 1.7;
  color: #1f2937;
  border-top: 1px dashed #d1d5db;
  padding-top: 12px;
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
