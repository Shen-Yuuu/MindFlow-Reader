<template>
  <div class="settings-view">
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title>设置</v-card-title>
          <v-divider></v-divider>
          
          <v-row>
            <!-- 侧边设置导航 -->
            <v-col cols="12" md="3" class="border-right">
              <v-list nav>
                <v-list-item
                  v-for="(item, i) in settingCategories"
                  :key="i"
                  :value="item.value"
                  :title="item.title"
                  :prepend-icon="item.icon"
                  @click="activeCategory = item.value"
                  :active="activeCategory === item.value"
                ></v-list-item>
              </v-list>
            </v-col>
            
            <!-- 主设置区域 -->
            <v-col cols="12" md="9">
              <div class="pa-4">
                <!-- 通用设置 -->
                <div v-if="activeCategory === 'general'">
                  <h2 class="text-h5 mb-4">通用设置</h2>
                  
                  <v-card variant="outlined" class="mb-4">
                    <v-card-title>个性化</v-card-title>
                    <v-card-text>
                      <v-switch
                        v-model="settings.darkMode"
                        label="深色模式"
                        color="primary"
                        hide-details
                        class="mb-2"
                      ></v-switch>
                      
                      <v-select
                        v-model="settings.language"
                        :items="languageOptions"
                        label="语言"
                        variant="outlined"
                        density="compact"
                        class="mb-2"
                      ></v-select>
                      
                      <v-select
                        v-model="settings.fontFamily"
                        :items="fontOptions"
                        label="字体"
                        variant="outlined"
                        density="compact"
                        class="mb-2"
                      ></v-select>
                      
                      <v-slider
                        v-model="settings.fontSize"
                        label="字体大小"
                        min="12"
                        max="24"
                        thumb-label
                        class="mt-4"
                      ></v-slider>
                    </v-card-text>
                  </v-card>
                  
                  <v-card variant="outlined">
                    <v-card-title>启动选项</v-card-title>
                    <v-card-text>
                      <v-select
                        v-model="settings.startupScreen"
                        :items="startupOptions"
                        label="启动页面"
                        variant="outlined"
                        density="compact"
                        class="mb-2"
                      ></v-select>
                      
                      <v-checkbox
                        v-model="settings.autoLoadLastDocument"
                        label="自动加载上次查看的文档"
                        color="primary"
                        hide-details
                      ></v-checkbox>
                    </v-card-text>
                  </v-card>
                </div>
                
                <!-- 阅读设置 -->
                <div v-if="activeCategory === 'reading'">
                  <h2 class="text-h5 mb-4">阅读设置</h2>
                  
                  <v-card variant="outlined" class="mb-4">
                    <v-card-title>阅读体验</v-card-title>
                    <v-card-text>
                      <v-slider
                        v-model="settings.lineSpacing"
                        label="行间距"
                        min="1"
                        max="2"
                        step="0.1"
                        thumb-label
                        class="mb-2"
                      ></v-slider>
                      
                      <v-select
                        v-model="settings.readerBackground"
                        :items="backgroundOptions"
                        label="背景颜色"
                        variant="outlined"
                        density="compact"
                        class="mb-2"
                      ></v-select>
                      
                      <v-switch
                        v-model="settings.enableAutoScroll"
                        label="启用自动滚动"
                        color="primary"
                        hide-details
                        class="mb-2"
                      ></v-switch>
                      
                      <v-checkbox
                        v-model="settings.highlightTerms"
                        label="自动高亮术语"
                        color="primary"
                        hide-details
                        class="mb-2"
                      ></v-checkbox>
                    </v-card-text>
                  </v-card>
                </div>
                
                <!-- AI设置 -->
                <div v-if="activeCategory === 'ai'">
                  <h2 class="text-h5 mb-4">AI设置</h2>
                  
                  <v-card variant="outlined" class="mb-4">
                    <v-card-title>AI服务配置</v-card-title>
                    <v-card-text>
                      <v-select
                        v-model="settings.aiModel"
                        :items="aiModelOptions"
                        label="AI模型"
                        variant="outlined"
                        density="compact"
                        class="mb-2"
                      ></v-select>
                      
                      <v-text-field
                        v-model="settings.apiKey"
                        label="API密钥"
                        variant="outlined"
                        density="compact"
                        type="password"
                        class="mb-4"
                      ></v-text-field>
                      
                      <v-checkbox
                        v-model="settings.useLocalModels"
                        label="优先使用本地模型"
                        color="primary"
                        hide-details
                        class="mb-2"
                      ></v-checkbox>
                    </v-card-text>
                  </v-card>
                  
                  <v-card variant="outlined">
                    <v-card-title>AI功能</v-card-title>
                    <v-card-text>
                      <v-checkbox
                        v-model="settings.enableConceptDetection"
                        label="启用概念检测"
                        color="primary"
                        hide-details
                        class="mb-2"
                      ></v-checkbox>
                      
                      <v-checkbox
                        v-model="settings.enableDifficultyPrediction"
                        label="启用难度预测"
                        color="primary"
                        hide-details
                        class="mb-2"
                      ></v-checkbox>
                      
                      <v-checkbox
                        v-model="settings.enableAutoSummarization"
                        label="启用自动摘要"
                        color="primary"
                        hide-details
                      ></v-checkbox>
                    </v-card-text>
                  </v-card>
                </div>
                
                <!-- 存储设置 -->
                <div v-if="activeCategory === 'storage'">
                  <h2 class="text-h5 mb-4">存储设置</h2>
                  
                  <v-card variant="outlined" class="mb-4">
                    <v-card-title>数据存储</v-card-title>
                    <v-card-text>
                      <v-select
                        v-model="settings.storageLocation"
                        :items="storageOptions"
                        label="存储位置"
                        variant="outlined"
                        density="compact"
                        class="mb-2"
                      ></v-select>
                      
                      <v-checkbox
                        v-model="settings.enableCloudSync"
                        label="启用云同步"
                        color="primary"
                        hide-details
                        class="mb-2"
                      ></v-checkbox>
                      
                      <div v-if="settings.enableCloudSync">
                        <v-text-field
                          v-model="settings.cloudUsername"
                          label="云账户用户名"
                          variant="outlined"
                          density="compact"
                          class="mt-4 mb-2"
                        ></v-text-field>
                        
                        <v-text-field
                          v-model="settings.cloudPassword"
                          label="云账户密码"
                          variant="outlined"
                          density="compact"
                          type="password"
                        ></v-text-field>
                      </div>
                    </v-card-text>
                  </v-card>
                  
                  <v-card variant="outlined">
                    <v-card-title>缓存管理</v-card-title>
                    <v-card-text>
                      <div class="d-flex align-center justify-space-between mb-2">
                        <div>缓存大小: 25MB</div>
                        <v-btn color="primary" variant="text">清除缓存</v-btn>
                      </div>
                      
                      <v-checkbox
                        v-model="settings.limitCacheSize"
                        label="限制缓存大小"
                        color="primary"
                        hide-details
                        class="mb-2"
                      ></v-checkbox>
                      
                      <v-slider
                        v-if="settings.limitCacheSize"
                        v-model="settings.maxCacheSize"
                        label="最大缓存大小(MB)"
                        min="50"
                        max="1000"
                        thumb-label
                      ></v-slider>
                    </v-card-text>
                  </v-card>
                </div>
              </div>
            </v-col>
          </v-row>
          
          <v-divider></v-divider>
          
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="primary" variant="text">保存设置</v-btn>
            <v-btn color="error" variant="text">重置为默认</v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const activeCategory = ref('general')

const settingCategories = [
  { title: '通用设置', value: 'general', icon: 'mdi-cog' },
  { title: '阅读设置', value: 'reading', icon: 'mdi-book-open-page-variant' },
  { title: 'AI设置', value: 'ai', icon: 'mdi-robot' },
  { title: '存储设置', value: 'storage', icon: 'mdi-database' }
]

const languageOptions = ['中文', '英文']
const fontOptions = ['默认', 'Roboto', 'Arial', 'Times New Roman']
const startupOptions = ['主页', '阅读器', '知识图谱', '个人知识库']
const backgroundOptions = ['白色', '米色', '浅灰', '黑色']
const aiModelOptions = ['本地轻量模型', 'OpenAI API', '自定义API']
const storageOptions = ['本地存储', '云存储']

const settings = ref({
  // 通用设置
  darkMode: false,
  language: '中文',
  fontFamily: '默认',
  fontSize: 16,
  startupScreen: '主页',
  autoLoadLastDocument: true,
  
  // 阅读设置
  lineSpacing: 1.5,
  readerBackground: '白色',
  enableAutoScroll: false,
  highlightTerms: true,
  
  // AI设置
  aiModel: '本地轻量模型',
  apiKey: '',
  useLocalModels: true,
  enableConceptDetection: true,
  enableDifficultyPrediction: true,
  enableAutoSummarization: false,
  
  // 存储设置
  storageLocation: '本地存储',
  enableCloudSync: false,
  cloudUsername: '',
  cloudPassword: '',
  limitCacheSize: false,
  maxCacheSize: 200
})
</script>

<style scoped>
.border-right {
  border-right: 1px solid rgba(0, 0, 0, 0.12);
}
</style> 