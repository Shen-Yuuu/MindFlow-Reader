<template>
  <v-app-bar app clipped-left elevation="1">
    <v-app-bar-nav-icon @click="toggleDrawer"></v-app-bar-nav-icon>
    
    <v-toolbar-title class="text-h6 font-weight-medium">
      MindFlow Reader
    </v-toolbar-title>
    
    <v-spacer></v-spacer>
    
    <v-btn icon class="mr-2">
      <v-icon>mdi-magnify</v-icon>
    </v-btn>
    
    <v-btn icon>
      <v-icon>mdi-bell</v-icon>
    </v-btn>
    
    <v-avatar class="ml-2" color="primary" size="36">
      <span class="text-h6 text-white">用户</span>
    </v-avatar>
  </v-app-bar>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'

const props = defineProps({
  navigationDrawer: Object
})

const $route = useRoute()

const toggleDrawer = () => {
  if (props.navigationDrawer) {
    props.navigationDrawer.drawer = !props.navigationDrawer.drawer
  }
}
</script> 