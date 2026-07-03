<template>
  <div class="home-container">
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>
    </div>

    <el-tabs v-model="activeAgentTab" class="agent-tabs" stretch>
      <el-tab-pane label="我的旅游Agent" name="travel" />
      <el-tab-pane label="我的聊天Agent" name="chat" />
      <el-tab-pane label="我的Agent模板二" name="template-2" />
    </el-tabs>

    <router-view />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const tabToRoute: Record<string, string> = {
  travel: '/agents/travel',
  chat: '/agents/chat',
  'template-2': '/agents/template-2'
}

const routeToTab: Record<string, string> = {
  '/agents/travel': 'travel',
  '/agents/chat': 'chat',
  '/agents/template-2': 'template-2'
}

const activeAgentTab = computed({
  get: () => routeToTab[route.path] ?? 'travel',
  set: (tabName: string) => {
    const targetPath = tabToRoute[tabName] ?? tabToRoute.travel
    router.push(targetPath)
  }
})
</script>

<style scoped>
.home-container {
  min-height: 100%;
  width: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 0;
  position: relative;
  overflow: hidden;
}

/* 背景装饰 */
.bg-decoration {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  overflow: hidden;
}

.circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  animation: float 20s infinite ease-in-out;
}

.circle-1 {
  width: 300px;
  height: 300px;
  top: -100px;
  left: -100px;
  animation-delay: 0s;
}

.circle-2 {
  width: 200px;
  height: 200px;
  top: 50%;
  right: -50px;
  animation-delay: 5s;
}

.circle-3 {
  width: 150px;
  height: 150px;
  bottom: -50px;
  left: 30%;
  animation-delay: 10s;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  50% {
    transform: translateY(-30px) rotate(180deg);
  }
}

.agent-tabs {
  max-width: 1400px;
  margin: 0 auto;
  padding: 10px 20px;
  position: relative;
  z-index: 1;
}

.agent-tabs :deep(.el-tabs__header) {
  margin-bottom: 0;
}

.agent-tabs :deep(.el-tabs__nav-wrap) {
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.92);
  padding: 4px;
}

.agent-tabs :deep(.el-tabs__item) {
  color: #34495e;
  font-size: 15px;
  font-weight: 600;
}

.agent-tabs :deep(.el-tabs__item.is-active) {
  color: #3a5cca;
}

.agent-tabs :deep(.el-tabs__active-bar) {
  height: 3px;
  border-radius: 999px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
}

</style>

