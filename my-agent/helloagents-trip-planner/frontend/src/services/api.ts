import axios from 'axios'
import type { TripFormData, TripPlanResponse } from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2分钟超时
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    console.log('发送请求:', config.method?.toUpperCase(), config.url)
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    console.log('收到响应:', response.status, response.config.url)
    return response
  },
  (error) => {
    console.error('响应错误:', error.response?.status, error.message)
    return Promise.reject(error)
  }
)

/**
 * 生成旅行计划
 */
export async function generateTripPlan(formData: TripFormData): Promise<TripPlanResponse> {
  try {
    const response = await apiClient.post<TripPlanResponse>('/api/trip/plan', formData)
    return response.data
  } catch (error: any) {
    console.error('生成旅行计划失败:', error)
    throw new Error(error.response?.data?.detail || error.message || '生成旅行计划失败')
  }
}

/**
 * 健康检查
 */
export async function healthCheck(): Promise<any> {
  try {
    const response = await apiClient.get('/health')
    return response.data
  } catch (error: any) {
    console.error('健康检查失败:', error)
    throw new Error(error.message || '健康检查失败')
  }
}

interface StreamChatOptions {
  onChunk: (chunk: string) => void | Promise<void>
  onError?: (message: string) => void
}

export interface ArticleSearchItem {
  title: string
  snippet: string
  url: string
}

interface StreamArticleOptions {
  onSearchResults: (payload: { rewritten_query: string; articles: ArticleSearchItem[] }) => void
  onChunk: (chunk: string) => void | Promise<void>
  onError?: (message: string) => void
}

/**
 * 聊天流式响应
 */
export async function streamChat(message: string, options: StreamChatOptions): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ message })
  })

  if (!response.ok || !response.body) {
    throw new Error(`聊天请求失败: ${response.status}`)
  }
  //获取二进制流读取器，分段读取后端返回的字节
  const reader = response.body.getReader()
  //二进制 Uint8Array → UTF-8 字符串
  const decoder = new TextDecoder('utf-8')
  //缓存不完整的分片数据（关键！防止一段 JSON 被切割在两次分片里）
  let buffer = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) {//后端流关闭，循环结束，聊天完成
      break
    }

    buffer += decoder.decode(value, { stream: true })
    const events = buffer.split('\n\n')
    buffer = events.pop() || ''

    for (const rawEvent of events) {
      const lines = rawEvent.split('\n')
      const eventLine = lines.find((line) => line.startsWith('event:'))
      const dataLine = lines.find((line) => line.startsWith('data:'))
      if (!eventLine || !dataLine) {
        continue
      }

      const eventName = eventLine.replace('event:', '').trim()
      let payload: any = {}
      try {
        payload = JSON.parse(dataLine.replace('data:', '').trim())
      } catch {
        payload = {}
      }

      if (eventName === 'chunk' && payload.content) {
        await options.onChunk(payload.content)
      }

      if (eventName === 'error' && options.onError) {
        options.onError(payload.message || '聊天失败')
      }
    }
  }
}

/**
 * 文章搜索与汇总流式响应
 */
export async function streamArticleSearch(
  query: string,
  options: StreamArticleOptions,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/article/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query, limit: 6 }),
  })

  if (!response.ok || !response.body) {
    throw new Error(`文章请求失败: ${response.status}`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) {
      break
    }

    buffer += decoder.decode(value, { stream: true })
    const events = buffer.split('\n\n')
    buffer = events.pop() || ''

    for (const rawEvent of events) {
      const lines = rawEvent.split('\n')
      const eventLine = lines.find((line) => line.startsWith('event:'))
      const dataLine = lines.find((line) => line.startsWith('data:'))
      if (!eventLine || !dataLine) {
        continue
      }

      const eventName = eventLine.replace('event:', '').trim()
      let payload: any = {}
      try {
        payload = JSON.parse(dataLine.replace('data:', '').trim())
      } catch {
        payload = {}
      }

      if (eventName === 'search_results') {
        options.onSearchResults({
          rewritten_query: payload.rewritten_query || '',
          articles: Array.isArray(payload.articles) ? payload.articles : [],
        })
      }

      if (eventName === 'chunk' && payload.content) {
        await options.onChunk(payload.content)
      }

      if (eventName === 'error' && options.onError) {
        options.onError(payload.message || '文章搜索失败')
      }
    }
  }
}

export default apiClient

