<template>
  <a-card class="form-card" :bordered="false">
    <a-form
      :model="formData"
      layout="vertical"
      @finish="handleSubmit"
    >
      <div class="form-section">
        <div class="section-header">
          <span class="section-icon">📍</span>
          <span class="section-title">目的地与日期</span>
        </div>

        <a-row :gutter="24">
          <a-col :span="8">
            <a-form-item name="city" :rules="[{ required: true, message: '请输入目的地城市' }]">
              <template #label>
                <span class="form-label">目的地城市</span>
              </template>
              <a-input
                v-model:value="formData.city"
                placeholder="例如: 北京"
                size="large"
                class="custom-input"
              >
                <template #prefix>
                  <span style="color: #1890ff;">🏙️</span>
                </template>
              </a-input>
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item name="start_date" :rules="[{ required: true, message: '请选择开始日期' }]">
              <template #label>
                <span class="form-label">开始日期</span>
              </template>
              <a-date-picker
                v-model:value="formData.start_date"
                style="width: 100%"
                size="large"
                class="custom-input"
                placeholder="选择日期"
              />
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item name="end_date" :rules="[{ required: true, message: '请选择结束日期' }]">
              <template #label>
                <span class="form-label">结束日期</span>
              </template>
              <a-date-picker
                v-model:value="formData.end_date"
                style="width: 100%"
                size="large"
                class="custom-input"
                placeholder="选择日期"
              />
            </a-form-item>
          </a-col>
          <a-col :span="4">
            <a-form-item>
              <template #label>
                <span class="form-label">旅行天数</span>
              </template>
              <div class="days-display-compact">
                <span class="days-value">{{ formData.travel_days }}</span>
                <span class="days-unit">天</span>
              </div>
            </a-form-item>
          </a-col>
        </a-row>
      </div>

      <div class="form-section">
        <div class="section-header">
          <span class="section-icon">⚙️</span>
          <span class="section-title">偏好设置</span>
        </div>

        <a-row :gutter="24">
          <a-col :span="8">
            <a-form-item name="transportation">
              <template #label>
                <span class="form-label">交通方式</span>
              </template>
              <a-select v-model:value="formData.transportation" size="large" class="custom-select">
                <a-select-option value="公共交通">🚇 公共交通</a-select-option>
                <a-select-option value="自驾">🚗 自驾</a-select-option>
                <a-select-option value="步行">🚶 步行</a-select-option>
                <a-select-option value="混合">🔀 混合</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item name="accommodation">
              <template #label>
                <span class="form-label">住宿偏好</span>
              </template>
              <a-select v-model:value="formData.accommodation" size="large" class="custom-select">
                <a-select-option value="经济型酒店">💰 经济型酒店</a-select-option>
                <a-select-option value="舒适型酒店">🏨 舒适型酒店</a-select-option>
                <a-select-option value="豪华酒店">⭐ 豪华酒店</a-select-option>
                <a-select-option value="民宿">🏡 民宿</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item name="preferences">
              <template #label>
                <span class="form-label">旅行偏好</span>
              </template>
              <div class="preference-tags">
                <a-checkbox-group v-model:value="formData.preferences" class="custom-checkbox-group">
                  <a-checkbox value="历史文化" class="preference-tag">🏛️ 历史文化</a-checkbox>
                  <a-checkbox value="自然风光" class="preference-tag">🏞️ 自然风光</a-checkbox>
                  <a-checkbox value="美食" class="preference-tag">🍜 美食</a-checkbox>
                  <a-checkbox value="购物" class="preference-tag">🛍️ 购物</a-checkbox>
                  <a-checkbox value="艺术" class="preference-tag">🎨 艺术</a-checkbox>
                  <a-checkbox value="休闲" class="preference-tag">☕ 休闲</a-checkbox>
                </a-checkbox-group>
              </div>
            </a-form-item>
          </a-col>
        </a-row>
      </div>

      <div class="form-section">
        <div class="section-header">
          <span class="section-icon">💬</span>
          <span class="section-title">额外要求</span>
        </div>

        <a-form-item name="free_text_input">
          <a-textarea
            v-model:value="formData.free_text_input"
            placeholder="请输入您的额外要求,例如:想去看升旗、需要无障碍设施、对海鲜过敏等..."
            :rows="3"
            size="large"
            class="custom-textarea"
          />
        </a-form-item>
      </div>

      <a-form-item>
        <a-button
          type="primary"
          html-type="submit"
          :loading="loading"
          size="large"
          block
          class="submit-button"
        >
          <template v-if="!loading">
            <span class="button-icon">🚀</span>
            <span>开始规划我的旅行</span>
          </template>
          <template v-else>
            <span>正在生成中...</span>
          </template>
        </a-button>
      </a-form-item>

      <a-form-item v-if="loading">
        <div class="loading-container">
          <a-progress
            :percent="loadingProgress"
            status="active"
            :stroke-color="{
              '0%': '#667eea',
              '100%': '#764ba2',
            }"
            :stroke-width="10"
          />
          <p class="loading-status">
            {{ loadingStatus }}
          </p>
        </div>
      </a-form-item>
    </a-form>
  </a-card>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import type { Dayjs } from 'dayjs'
import { generateTripPlan } from '@/services/api'
import type { TripFormData } from '@/types'

type TravelAgentFormData = Omit<TripFormData, 'start_date' | 'end_date'> & {
  start_date: Dayjs | null
  end_date: Dayjs | null
}

const router = useRouter()
const loading = ref(false)
const loadingProgress = ref(0)
const loadingStatus = ref('')

const formData = reactive<TravelAgentFormData>({
  city: '',
  start_date: null,
  end_date: null,
  travel_days: 1,
  transportation: '公共交通',
  accommodation: '经济型酒店',
  preferences: [],
  free_text_input: ''
})

watch([() => formData.start_date, () => formData.end_date], ([start, end]) => {
  if (start && end) {
    const days = end.diff(start, 'day') + 1
    if (days > 0 && days <= 30) {
      formData.travel_days = days
    } else if (days > 30) {
      message.warning('旅行天数不能超过30天')
      formData.end_date = null
    } else {
      message.warning('结束日期不能早于开始日期')
      formData.end_date = null
    }
  }
})

const handleSubmit = async () => {
  if (!formData.start_date || !formData.end_date) {
    message.error('请选择日期')
    return
  }

  loading.value = true
  loadingProgress.value = 0
  loadingStatus.value = '正在初始化...'

  const progressInterval = setInterval(() => {
    if (loadingProgress.value < 90) {
      loadingProgress.value += 10

      if (loadingProgress.value <= 30) {
        loadingStatus.value = '🔍 正在搜索景点...'
      } else if (loadingProgress.value <= 50) {
        loadingStatus.value = '🌤️ 正在查询天气...'
      } else if (loadingProgress.value <= 70) {
        loadingStatus.value = '🏨 正在推荐酒店...'
      } else {
        loadingStatus.value = '📋 正在生成行程计划...'
      }
    }
  }, 500)

  try {
    const requestData: TripFormData = {
      city: formData.city,
      start_date: formData.start_date.format('YYYY-MM-DD'),
      end_date: formData.end_date.format('YYYY-MM-DD'),
      travel_days: formData.travel_days,
      transportation: formData.transportation,
      accommodation: formData.accommodation,
      preferences: formData.preferences,
      free_text_input: formData.free_text_input
    }

    const response = await generateTripPlan(requestData)

    clearInterval(progressInterval)
    loadingProgress.value = 100
    loadingStatus.value = '✅ 完成!'

    if (response.success && response.data) {
      sessionStorage.setItem('tripPlan', JSON.stringify(response.data))

      message.success('旅行计划生成成功!')

      setTimeout(() => {
        router.push('/result')
      }, 500)
    } else {
      message.error(response.message || '生成失败')
    }
  } catch (error: any) {
    clearInterval(progressInterval)
    message.error(error.message || '生成旅行计划失败,请稍后重试')
  } finally {
    setTimeout(() => {
      loading.value = false
      loadingProgress.value = 0
      loadingStatus.value = ''
    }, 1000)
  }
}
</script>

<style scoped>
.form-card {
  max-width: 1400px;
  margin: 0 auto;
  border-radius: 24px;
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.4);
  animation: fadeInUp 0.8s ease-out;
  position: relative;
  z-index: 1;
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.98) !important;
}

.form-section {
  margin-bottom: 32px;
  padding: 24px;
  background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
  border-radius: 16px;
  border: 1px solid #e8e8e8;
  transition: all 0.3s ease;
}

.form-section:hover {
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.15);
  transform: translateY(-2px);
}

.section-header {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid #667eea;
}

.section-icon {
  font-size: 24px;
  margin-right: 12px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.form-label {
  font-size: 15px;
  font-weight: 500;
  color: #555;
}

.custom-input :deep(.ant-input),
.custom-input :deep(.ant-picker) {
  border-radius: 12px;
  border: 2px solid #e8e8e8;
  transition: all 0.3s ease;
}

.custom-input :deep(.ant-input:hover),
.custom-input :deep(.ant-picker:hover) {
  border-color: #667eea;
}

.custom-input :deep(.ant-input:focus),
.custom-input :deep(.ant-picker-focused) {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.custom-select :deep(.ant-select-selector) {
  border-radius: 12px !important;
  border: 2px solid #e8e8e8 !important;
  transition: all 0.3s ease;
}

.custom-select:hover :deep(.ant-select-selector) {
  border-color: #667eea !important;
}

.custom-select :deep(.ant-select-focused .ant-select-selector) {
  border-color: #667eea !important;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
}

.days-display-compact {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 40px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
}

.days-display-compact .days-value {
  font-size: 24px;
  font-weight: 700;
  margin-right: 4px;
}

.days-display-compact .days-unit {
  font-size: 14px;
}

.preference-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.custom-checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  width: 100%;
}

.preference-tag :deep(.ant-checkbox-wrapper) {
  margin: 0 !important;
  padding: 8px 16px;
  border: 2px solid #e8e8e8;
  border-radius: 20px;
  transition: all 0.3s ease;
  background: white;
  font-size: 14px;
}

.preference-tag :deep(.ant-checkbox-wrapper:hover) {
  border-color: #667eea;
  background: #f5f7ff;
}

.preference-tag :deep(.ant-checkbox-wrapper-checked) {
  border-color: #667eea;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.custom-textarea :deep(.ant-input) {
  border-radius: 12px;
  border: 2px solid #e8e8e8;
  transition: all 0.3s ease;
}

.custom-textarea :deep(.ant-input:hover) {
  border-color: #667eea;
}

.custom-textarea :deep(.ant-input:focus) {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.submit-button {
  height: 56px;
  border-radius: 28px;
  font-size: 18px;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
  transition: all 0.3s ease;
}

.submit-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(102, 126, 234, 0.5);
}

.submit-button:active {
  transform: translateY(0);
}

.button-icon {
  margin-right: 8px;
  font-size: 20px;
}

.loading-container {
  text-align: center;
  padding: 24px;
  background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
  border-radius: 16px;
  border: 2px dashed #667eea;
}

.loading-status {
  margin-top: 16px;
  color: #667eea;
  font-size: 18px;
  font-weight: 500;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
