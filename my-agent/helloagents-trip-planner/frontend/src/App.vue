<template>
  <div id="app">
    <el-container style="min-height: 100vh">
      <el-header style="background: #001529; padding: 0 50px; display: flex; align-items: center;">
        <div style="color: white; font-size: 24px; font-weight: bold;">
          🤖 HelloAgents我的Agent管家
        </div>
      </el-header>
      <el-main style="padding: 24px">
        <router-view />
      </el-main>
      <el-footer style="text-align: center">
        HelloAgents我的Agent管家 ©2025 基于HelloAgents框架
      </el-footer>
    </el-container>
  </div>
</template>

<script setup lang="ts">
</script>

<style>
#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    'Noto Sans', sans-serif;
}
</style>

