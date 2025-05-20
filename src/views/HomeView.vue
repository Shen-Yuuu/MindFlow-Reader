<script setup lang="ts">
const features = [
  {
    icon: 'mdi-brain',
    title: '智能文献预处理',
    description: '自动分析文献结构、提取关键概念和参考文献'
  },
  {
    icon: 'mdi-lightbulb',
    title: '实时辅助交互',
    description: '阅读过程中提供术语解释和智能导航'
  },
  {
    icon: 'mdi-chart-network',
    title: '知识图谱构建',
    description: '自动构建概念关系图，帮助理解复杂关系'
  },
  {
    icon: 'mdi-tune',
    title: '心流维持',
    description: '专注模式与个性化设置保持最佳阅读状态'
  }
]
</script>

<template>
  <div class="home">
    <v-row>
      <v-col cols="12">
        <v-card class="mx-auto" width="800" height="900">
          <v-img
            src="https://images.unsplash.com/photo-1532153975070-2e9ab71f1b14?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80"
            height="300px"
            cover
          ></v-img>
          <v-card-title class="text-h4">欢迎使用 MindFlow Reader</v-card-title>
          <v-card-subtitle>专注的学术文献阅读体验</v-card-subtitle>
          <v-card-text class="mt-4" style="height: 280px;">
            <p>MindFlow Reader 是一个功能完整的学术文献阅读Web应用，内置多种AI模型辅助实现核心功能，旨在为研究人员提供流畅的心流阅读体验。</p>
            <v-divider class="my-4"></v-divider>
            <v-row class="mt-4">
              <v-col v-for="(feature, i) in features" :key="i" cols="12" md="6">
                <div class="d-flex align-center">
                  <v-icon size="large" color="primary" class="mr-3">{{ feature.icon }}</v-icon>
                  <div>
                    <h3 class="text-subtitle-1 font-weight-bold">{{ feature.title }}</h3>
                    <p class="text-body-2">{{ feature.description }}</p>
                  </div>
                </div>
              </v-col>
            </v-row>
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="primary" to="/reader">
              开始阅读
              <v-icon end>mdi-arrow-right</v-icon>
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>
