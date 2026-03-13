<template>
  <el-container class="app-layout">
    <el-aside width="220px" class="app-sidebar">
      <div class="sidebar-logo">
        <h1>CCSwitch</h1>
      </div>
      <el-menu :default-active="activeMenu" router class="sidebar-menu" background-color="#1d1e2c" text-color="#a3a6ad" active-text-color="#409eff">
        <el-menu-item index="/">
          <el-icon><DataBoard /></el-icon>
          <span>项目总览</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-main class="app-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activeMenu = computed(() => route.path === '/' ? '/' : route.path)
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
}
.app-sidebar {
  background-color: #1d1e2c;
  overflow: hidden;
}
.sidebar-logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid #2d2e3e;
}
.sidebar-logo h1 {
  color: #409eff;
  font-size: 22px;
  letter-spacing: 2px;
}
.sidebar-menu {
  border-right: none;
}
.app-main {
  background-color: #f5f7fa;
  padding: 20px;
}
</style>
