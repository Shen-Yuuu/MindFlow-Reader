<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { RouterView } from 'vue-router'
import AppNavigation from './components/AppNavigation.vue'

</script>

<template>
  <v-app>
    <AppNavigation /> 
    
    <v-app-bar app density="compact"> 
      <div class="d-flex align-center">
        <h1 class="text-h6 ml-3">MindFlow</h1>
      </div>
      <v-spacer></v-spacer> 
      <v-btn text>用户</v-btn> 
    </v-app-bar>

    <v-main style="--v-layout-left: 0px;">
      <div class="app-container" style="">
        <RouterView />
      </div>
    </v-main>

    <!-- 移除 Footer 或使其更简洁 -->
    <!-- <v-footer app height="30"> /* 减小页脚高度 */
      <span>&copy; {{ new Date().getFullYear() }} MindFlow</span>
    </v-footer> -->
  </v-app>
</template>

<style>
html, body {
  height: 100%;
  width: 100%;
  margin: 0;
  padding: 0;
  overflow: hidden; /* 防止顶层滚动 */
  font-family: 'Roboto', sans-serif;
}

#app, .v-application {
  height: 100%;
  width: 100%;
}

.app-container {
  padding: 5px; /* 移除内边距，让 RouterView 完全填充 */
  height: 100%; 
  width: 100%;
  overflow: hidden; /* 防止此层级滚动 */
}

.v-main {
  height: calc(100vh - 48px);
  overflow: hidden; 
}


</style>
