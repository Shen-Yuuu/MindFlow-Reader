<template>
  <div class="navigation-container">
    <!-- 切换抽屉按钮 -->
    <v-btn
      icon
      size="small"
      :class="{'toggle-button': true, 'toggle-button-closed': !drawer}"
      @click="toggleDrawer"
      title="切换导航栏"
    >
      <v-icon>{{ drawer ? 'mdi-chevron-left' : 'mdi-chevron-right' }}</v-icon>
    </v-btn>

    <v-navigation-drawer
      app
      class="primary-navigation"
      v-model="drawer"
      :width="drawerWidth"
      permanent
    >
      <v-list nav>
        <v-list-item to="/reader" prepend-icon="mdi-book-open-variant" title="文献阅读" value="reader"></v-list-item>
        <v-list-item to="/knowledge-graph" prepend-icon="mdi-graph" title="知识图谱" value="knowledge-graph"></v-list-item>
        <v-list-item to="/knowledge-base" prepend-icon="mdi-brain" title="个人知识库" value="knowledge-base"></v-list-item>
        <v-list-item to="/settings" prepend-icon="mdi-cog" title="设置" value="settings"></v-list-item>
      </v-list>
    </v-navigation-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const drawer = ref(true)

// 计算抽屉宽度
const drawerWidth = computed(() => drawer.value ? 200 : 0)

// 切换抽屉状态
function toggleDrawer() {
  drawer.value = !drawer.value
}

// 向父组件暴露drawer变量
defineExpose({
  drawer
})
</script>

<style scoped>
.primary-navigation {
  transition: width 0.3s ease;
  overflow: hidden;
  background-color: white;
}

.navigation-container {
  position: relative;
}

.toggle-button {
  position: absolute;
  top: 10px;
  right: -18px;
  z-index: 1000;
  background-color: white;
  border: 1px solid rgba(0, 0, 0, 0.1);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.toggle-button-closed {
  right: 10px;
  transform: translateX(-100%);
}

.primary-navigation:not(.v-navigation-drawer--active) + .toggle-button {
  /* display: none;  如果需要，取消注释 */
}
</style> 