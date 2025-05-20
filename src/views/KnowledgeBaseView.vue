<template>
  <div class="knowledge-base-view">
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <div>
              个人知识库
              <v-chip small color="primary" class="ml-2">预览版</v-chip>
            </div>
            <v-spacer></v-spacer>
            <v-btn icon title="设置">
              <v-icon>mdi-cog</v-icon>
            </v-btn>
          </v-card-title>
          
          <v-divider></v-divider>
          
          <v-row>
            <!-- 侧边目录 -->
            <v-col cols="12" md="3" class="border-right">
              <v-list>
                <v-list-subheader>文献分类</v-list-subheader>
                <v-list-item v-for="(category, index) in categories" :key="index" :title="category.name"
                           :subtitle="`${category.count}篇文献`" :prepend-icon="category.icon"></v-list-item>
                
                <v-divider class="my-2"></v-divider>
                
                <v-list-subheader>标签</v-list-subheader>
                <div class="pa-3">
                  <v-chip v-for="(tag, index) in tags" :key="index" class="ma-1" size="small" color="primary" variant="outlined">
                    {{ tag.name }} ({{ tag.count }})
                  </v-chip>
                </div>
              </v-list>
            </v-col>
            
            <!-- 主内容区域 -->
            <v-col cols="12" md="9">
              <div class="pa-4">
                <v-text-field prepend-inner-icon="mdi-magnify" label="搜索知识库" variant="outlined"
                             hide-details class="mb-4"></v-text-field>
                
                <v-tabs v-model="activeTab" class="mb-4">
                  <v-tab value="recent">最近阅读</v-tab>
                  <v-tab value="notes">我的笔记</v-tab>
                  <v-tab value="collections">收藏集</v-tab>
                </v-tabs>
                
                <v-window v-model="activeTab">
                  <v-window-item value="recent">
                    <v-row>
                      <v-col v-for="(article, index) in recentArticles" :key="index" cols="12" md="6" lg="4">
                        <v-card variant="outlined" class="h-100">
                          <v-card-item>
                            <v-card-title>{{ article.title }}</v-card-title>
                            <v-card-subtitle>{{ article.authors.join(', ') }}</v-card-subtitle>
                          </v-card-item>
                          <v-divider></v-divider>
                          <v-card-text>
                            <div class="text-truncate mb-2">{{ article.abstract }}</div>
                            <div class="d-flex align-center">
                              <v-icon size="small" color="grey">mdi-clock-outline</v-icon>
                              <span class="text-caption text-grey ml-1">最近阅读: {{ article.lastRead }}</span>
                            </div>
                          </v-card-text>
                          <v-divider></v-divider>
                          <v-card-actions>
                            <v-btn variant="text" color="primary" size="small">
                              <v-icon start>mdi-book-open-variant</v-icon>
                              继续阅读
                            </v-btn>
                            <v-spacer></v-spacer>
                            <v-btn icon size="small">
                              <v-icon>mdi-bookmark-outline</v-icon>
                            </v-btn>
                          </v-card-actions>
                        </v-card>
                      </v-col>
                    </v-row>
                  </v-window-item>
                  
                  <v-window-item value="notes">
                    <div class="text-center pa-12">
                      <v-icon size="large" color="grey lighten-1">mdi-notebook-outline</v-icon>
                      <p class="text-h6 mt-4 text-grey-darken-1">暂无笔记</p>
                      <p class="text-body-1 text-grey">在阅读过程中添加笔记将会显示在这里</p>
                    </div>
                  </v-window-item>
                  
                  <v-window-item value="collections">
                    <div class="text-center pa-12">
                      <v-icon size="large" color="grey lighten-1">mdi-bookshelf</v-icon>
                      <p class="text-h6 mt-4 text-grey-darken-1">暂无收藏集</p>
                      <p class="text-body-1 text-grey">您可以创建收藏集来整理您的文献</p>
                      <v-btn color="primary" class="mt-4" prepend-icon="mdi-plus">
                        创建收藏集
                      </v-btn>
                    </div>
                  </v-window-item>
                </v-window>
              </div>
            </v-col>
          </v-row>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const activeTab = ref('recent')

const categories = [
  { name: '所有文献', count: 0, icon: 'mdi-file-document-multiple' },
  { name: '已阅读', count: 0, icon: 'mdi-eye' },
  { name: '未阅读', count: 0, icon: 'mdi-eye-off' },
  { name: '已标记', count: 0, icon: 'mdi-bookmark' }
]

const tags = [
  { name: 'AI', count: 0 },
  { name: '机器学习', count: 0 },
  { name: '知识图谱', count: 0 },
  { name: '认知科学', count: 0 },
  { name: '心理学', count: 0 }
]

const recentArticles = [
  {
    title: '示例文献标题',
    authors: ['作者1', '作者2'],
    abstract: '这是一个示例文献摘要，描述了该研究的主要目的和发现。在实际应用中，这里将显示文献的真实摘要内容。',
    lastRead: '2小时前'
  }
]
</script>

<style scoped>
.border-right {
  border-right: 1px solid rgba(0, 0, 0, 0.12);
}
</style> 