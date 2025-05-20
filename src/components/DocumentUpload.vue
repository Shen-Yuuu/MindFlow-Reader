<template>
  <div class="document-upload">
    <v-dialog v-model="dialog" max-width="600">
      <template v-slot:activator="{ props }">
        <v-btn
          color="primary"
          v-bind="props"
          block
          prepend-icon="mdi-upload"
        >
          导入文献
        </v-btn>
      </template>

      <v-card>
        <v-card-title class="text-h5">
          导入文献
        </v-card-title>
        
        <v-card-text>
          <v-file-input
            v-model="files"
            label="选择PDF文件"
            accept="application/pdf"
            multiple
            prepend-icon="mdi-file-document"
            show-size
            chips
            counter
            truncate-length="15"
            :rules="[v => !!v || '请选择文件']"
          ></v-file-input>
          
          <v-alert
            v-if="uploadError"
            type="error"
            variant="tonal"
            class="mt-3"
            closable
          >
            {{ uploadError }}
          </v-alert>
          
          <v-card v-if="files?.length" class="mt-4" variant="outlined">
            <v-card-title class="text-subtitle-1">预处理选项</v-card-title>
            <v-card-text>
              <v-checkbox
                v-model="options.extractConcepts"
                label="自动提取关键概念"
                density="compact"
                hide-details
                class="mb-2"
              ></v-checkbox>
              
              <v-checkbox
                v-model="options.buildKnowledgeGraph"
                label="构建知识图谱"
                density="compact"
                hide-details
                class="mb-2"
              ></v-checkbox>
              
              <v-checkbox
                v-model="options.difficultyPrediction"
                label="预测认知难点"
                density="compact"
                hide-details
              ></v-checkbox>
            </v-card-text>
          </v-card>
        </v-card-text>
        
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            color="grey-darken-1"
            variant="text"
            @click="dialog = false"
          >
            取消
          </v-btn>
          <v-btn
            color="primary"
            @click="uploadDocuments"
            :loading="isUploading"
            :disabled="!files?.length"
          >
            上传
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useDocumentStore, type Document } from '@/stores/documents'

const documentStore = useDocumentStore()

const dialog = ref(false)
const files = ref<File[]>([])
const uploadError = ref('')
const isUploading = ref(false)

const options = ref({
  extractConcepts: true,
  buildKnowledgeGraph: true,
  difficultyPrediction: false
})

async function uploadDocuments() {
  if (!files.value || files.value.length === 0) {
    uploadError.value = '请选择要上传的文件'
    return
  }

  isUploading.value = true
  uploadError.value = ''

  try {
    // 在实际应用中，这里会调用后端API处理文件
    // 这里我们模拟文件上传和处理
    await simulateFileProcessing()

    // 添加文档到存储
    for (const file of files.value) {
      const newDoc: Document = {
        id: Date.now() + Math.random().toString(36).substr(2, 9),
        title: file.name.replace(/\.[^/.]+$/, ""), // 移除扩展名作为标题
        authors: ['待提取'], // 实际应用中会从PDF中提取
        year: new Date().getFullYear().toString(),
        abstract: '正在处理文献内容...',
        content: ['文献内容正在处理中，请稍后查看...'],
        fileName: file.name,
        fileType: file.type,
        fileSize: file.size,
        uploadDate: new Date(),
        lastReadDate: new Date(),
        tags: [],
        concepts: []
      }
      
      documentStore.addDocument(newDoc)
    }

    dialog.value = false
    files.value = []
    isUploading.value = false
  } catch (error) {
    uploadError.value = '上传失败: ' + (error instanceof Error ? error.message : String(error))
    isUploading.value = false
  }
}

// 模拟文件处理延迟
function simulateFileProcessing() {
  return new Promise(resolve => setTimeout(resolve, 1500))
}
</script> 