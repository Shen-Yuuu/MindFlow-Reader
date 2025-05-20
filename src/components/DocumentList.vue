<template>
  <div class="document-list">
    <div class="list-header">
      <div class="search-upload-container">
        <v-text-field
          v-model="searchQuery"
          prepend-inner-icon="mdi-magnify"
          label="搜索文档"
          density="compact"
          hide-details
          clearable
          class="search-field"
        />
        <v-tooltip location="top" text="上传新文献">
          <template v-slot:activator="{ props }">
            <v-btn
              color="primary"
              @click="showUploadDialog = true"
              prepend-icon="mdi-upload"
              variant="tonal"
              size="small"
              v-bind="props"
            >
              上传
            </v-btn>
          </template>
        </v-tooltip>
      </div>
      
      <div class="filter-result" v-if="searchQuery">
        <v-chip closable @click:close="searchQuery = ''" size="small" color="primary" variant="outlined">
          搜索结果: {{ filteredDocuments.length }} 项
        </v-chip>
      </div>
      
      <div class="filter-tabs">
        <v-tabs
          v-model="activeTab"
          density="comfortable"
          color="primary"
          align-tabs="start"
        >
          <v-tab value="all">全部</v-tab>
          <v-tab value="recent">最近</v-tab>
          <v-tab value="favorites">收藏</v-tab>
          <v-tab value="unread">未读</v-tab>
        </v-tabs>
      </div>
    </div>
    
    <div class="list-content">
      <div v-if="loading" class="loading-state">
        <v-progress-circular indeterminate color="primary" />
        <span class="loading-text">加载文档中...</span>
      </div>
      
      <div v-else-if="filteredDocuments.length === 0" class="empty-state">
        <v-icon size="64" color="grey-lighten-1">mdi-file-document-outline</v-icon>
        <p class="empty-text">{{ searchQuery ? '没有找到匹配的文档' : '还没有导入文档' }}</p>
        <v-btn
          v-if="!searchQuery"
          color="primary"
          variant="tonal"
          @click="showUploadDialog = true"
          prepend-icon="mdi-upload"
          class="mt-4"
        >
          导入文档
        </v-btn>
        <v-btn
          v-else
          color="primary"
          variant="text"
          @click="searchQuery = ''"
          prepend-icon="mdi-refresh"
          class="mt-4"
        >
          清除搜索
        </v-btn>
      </div>
      
      <v-list v-else lines="two" class="document-items">
        <v-list-item
          v-for="doc in filteredDocuments"
          :key="doc.id"
          :active="documentStore.currentDocumentId === doc.id"
          @click="selectDocument(doc)"
          :link="true"
          class="document-list-item"
          :class="{'document-item-active': documentStore.currentDocumentId === doc.id}"
        >
          <template v-slot:prepend>
            <v-checkbox
              v-model="doc.selected"
              @click.stop
              hide-details
              density="compact"
            />
          </template>
          
          <v-list-item-title class="text-truncate font-weight-medium">
            {{ doc.title }}
          </v-list-item-title>
          
          <v-list-item-subtitle class="text-truncate">
            {{ doc.authors.join(', ') }} ({{ doc.year }})
          </v-list-item-subtitle>
          
          <template v-slot:append>
            <div class="document-actions">
              <v-btn
                icon="mdi-eye"
                variant="text"
                size="small"
                @click.stop="viewDocument(doc)"
                color="primary"
              />
              <v-btn
                icon="mdi-download"
                variant="text"
                size="small"
                @click.stop="downloadDocument(doc)"
                color="grey"
              />
              <v-menu>
                <template v-slot:activator="{ props }">
                  <v-btn
                    icon="mdi-dots-vertical"
                    variant="text"
                    size="small"
                    v-bind="props"
                    @click.stop
                    class="menu-button"
                  />
                </template>
                <v-list density="compact">
                  <v-list-item @click.stop="toggleFavorite(doc)">
                    <v-list-item-title>
                      <v-icon 
                        :color="doc.favorite ? 'amber' : 'grey'"
                        class="mr-2"
                      >
                        {{ doc.favorite ? 'mdi-star' : 'mdi-star-outline' }}
                      </v-icon>
                      {{ doc.favorite ? '取消收藏' : '添加收藏' }}
                    </v-list-item-title>
                  </v-list-item>
                  <v-list-item @click.stop="showDocDetails(doc)">
                    <v-list-item-title>
                      <v-icon class="mr-2">mdi-information-outline</v-icon>
                      查看详情
                    </v-list-item-title>
                  </v-list-item>
                  <v-list-item @click.stop="deleteDocument(doc)">
                    <v-list-item-title class="text-red">
                      <v-icon color="red" class="mr-2">mdi-delete-outline</v-icon>
                      删除
                    </v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-menu>
            </div>
          </template>
        </v-list-item>
      </v-list>
    </div>
    
    <!-- 上传对话框 -->
    <v-dialog v-model="showUploadDialog" max-width="600">
      <v-card>
        <v-card-title class="d-flex justify-space-between align-center">
          <span>导入文档</span>
          <v-btn icon="mdi-close" variant="text" @click="showUploadDialog = false" />
        </v-card-title>
        
        <v-card-text>
          <v-tabs v-model="uploadTab">
            <v-tab value="file">文件上传</v-tab>
            <v-tab value="doi">DOI导入</v-tab>
            <v-tab value="url">URL导入</v-tab>
          </v-tabs>
          
          <v-window v-model="uploadTab" class="mt-4">
            <!-- 文件上传 -->
            <v-window-item value="file">
              <v-file-input
                v-model="uploadFiles"
                label="选择PDF文件"
                accept="application/pdf"
                prepend-icon="mdi-file-pdf-box"
                show-size
                multiple
                chips
                :clearable="true"
              />
              <p class="text-caption mt-2">支持PDF文件，最大50MB</p>
            </v-window-item>
            
            <!-- DOI导入 -->
            <v-window-item value="doi">
              <v-text-field
                v-model="doiInput"
                label="输入DOI"
                hint="例如: 10.1038/s41586-020-2649-2"
                persistent-hint
                prepend-inner-icon="mdi-identifier"
              />
            </v-window-item>
            
            <!-- URL导入 -->
            <v-window-item value="url">
              <v-text-field
                v-model="urlInput"
                label="输入URL"
                hint="输入PDF的URL地址"
                persistent-hint
                prepend-inner-icon="mdi-link"
                type="url"
              />
            </v-window-item>
          </v-window>
        </v-card-text>
        
        <v-card-actions>
          <v-spacer />
          <v-btn
            variant="text"
            @click="showUploadDialog = false"
          >
            取消
          </v-btn>
          <v-btn
            color="primary"
            @click="handleDialogConfirm"
            :loading="uploading"
            :disabled="!canUpload"
          >
            导入
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    
    <!-- 文档详情对话框 -->
    <v-dialog v-model="showDocDetailsDialog" max-width="700">
      <v-card v-if="detailDocument">
        <v-card-title class="d-flex justify-space-between align-center">
          <span>文档详情</span>
          <v-btn icon="mdi-close" variant="text" @click="showDocDetailsDialog = false" />
        </v-card-title>
        
        <v-card-text>
          <div class="doc-details">
            <h2 class="text-h5 mb-2">{{ detailDocument.title }}</h2>
            
            <div class="detail-item">
              <div class="detail-label">作者</div>
              <div class="detail-value">{{ detailDocument.authors.join(', ') }}</div>
            </div>
            
            <div class="detail-item">
              <div class="detail-label">期刊</div>
              <div class="detail-value">{{ detailDocument.journal || '未知' }}</div>
            </div>
            
            <div class="detail-item">
              <div class="detail-label">年份</div>
              <div class="detail-value">{{ detailDocument.year || '未知' }}</div>
            </div>
            
            <div class="detail-item" v-if="detailDocument.doi">
              <div class="detail-label">DOI</div>
              <div class="detail-value">
                <a :href="`https://doi.org/${detailDocument.doi}`" target="_blank">
                  {{ detailDocument.doi }}
                </a>
              </div>
            </div>
            
            <div class="detail-item" v-if="detailDocument.abstract">
              <div class="detail-label">摘要</div>
              <div class="detail-value abstract-text">{{ detailDocument.abstract }}</div>
            </div>
            
            <div class="detail-item" v-if="detailDocument.keywords && detailDocument.keywords.length > 0">
              <div class="detail-label">关键词</div>
              <div class="detail-value">
                <v-chip
                  v-for="(keyword, index) in detailDocument.keywords"
                  :key="index"
                  size="small"
                  class="mr-1 mb-1"
                  color="primary"
                  variant="tonal"
                >
                  {{ keyword }}
                </v-chip>
              </div>
            </div>
            
            <div class="detail-item">
              <div class="detail-label">添加日期</div>
              <div class="detail-value">{{ formatDate(detailDocument.addedDate) }}</div>
            </div>
            
            <div class="detail-item">
              <div class="detail-label">文件大小</div>
              <div class="detail-value">{{ formatFileSize(detailDocument.fileSize) }}</div>
            </div>
          </div>
        </v-card-text>
        
        <v-card-actions>
          <v-spacer />
          <v-btn
            color="primary"
            variant="tonal"
            prepend-icon="mdi-pencil"
            @click="editDocDetails"
          >
            编辑信息
          </v-btn>
          <v-btn
            color="primary"
            prepend-icon="mdi-eye"
            @click="viewAndCloseDetails"
          >
            阅读文档
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useDocumentStore, type Document } from '../stores/documents'
import axios from 'axios'

const documentStore = useDocumentStore()
const props = defineProps({
  selectedDocumentId: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['select-document'])

// 状态
const loading = ref(false)
const selectedDocument = ref(null)
const searchQuery = ref('')
const activeTab = ref('all')
const showUploadDialog = ref(false)
const uploadTab = ref('file')
const uploadFiles = ref([])
const doiInput = ref('')
const urlInput = ref('')
const showDocDetailsDialog = ref(false)
const detailDocument = ref(null)
const uploading = ref(false)

// Define the backend response type locally or import from store/types
interface UploadedDocData {
  id: string;
  title: string;
  concepts: Array<{ term: string, definition: string | null }>;
}

// 上传方法
const canUpload = computed(() => {
  if (uploadTab.value === 'file') {
    return uploadFiles.value && uploadFiles.value.length > 0
  } else if (uploadTab.value === 'doi') {
    return doiInput.value && doiInput.value.trim().length > 0
  } else if (uploadTab.value === 'url') {
    return urlInput.value && urlInput.value.trim().length > 0
  }
  return false
})

// 文档过滤
const filteredDocuments = computed(() => {
  let docs = documentStore.documents
  
  // 基于标签过滤
  if (activeTab.value === 'recent') {
    docs = [...docs].sort((a, b) => new Date(b.lastReadDate) - new Date(a.lastReadDate))
    docs = docs.slice(0, 10) // 最近10个
  } else if (activeTab.value === 'favorites') {
    docs = docs.filter(doc => doc.favorite)
  } else if (activeTab.value === 'unread') {
    docs = docs.filter(doc => !doc.readStatus || doc.readStatus === 'unread')
  }
  
  // 基于搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    docs = docs.filter(doc => 
      doc.title.toLowerCase().includes(query) ||
      doc.authors.some(author => author.toLowerCase().includes(query)) ||
      (doc.abstract && doc.abstract.toLowerCase().includes(query)) ||
      (doc.keywords && doc.keywords.some(kw => kw.toLowerCase().includes(query)))
    )
  }
  
  return docs
})

// 文档操作方法
const selectDocument = (doc) => {
  // 将当前文档设置到store中
  documentStore.setCurrentDocument(doc.id)
  // 触发选择事件，将文档ID传递给父组件
  emit('select-document', doc)
}

const viewDocument = (doc) => {
  selectDocument(doc)
}

const downloadDocument = (doc) => {
  // 实现下载逻辑
  console.log('下载文档:', doc.title)
  // 模拟下载操作
  const link = document.createElement('a')
  link.href = doc.downloadUrl || '#'
  link.download = `${doc.title}.pdf`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const toggleFavorite = (doc) => {
  documentStore.updateDocument(doc.id, {
    favorite: !doc.favorite
  })
}

const deleteDocument = (doc) => {
  if (confirm(`确定要删除文档"${doc.title}"吗？`)) {
    documentStore.removeDocument(doc.id)
    if (selectedDocument.value?.id === doc.id) {
      selectedDocument.value = null
      emit('select-document', null)
    }
  }
}

const handleDialogConfirm = async () => {
  console.log('[DocumentList] Import button clicked');
  
  // --- File Upload Logic ---
  if (uploadTab.value === 'file' && uploadFiles.value.length > 0) {
    uploading.value = true;
    console.log(`[DocumentList] Starting upload for ${uploadFiles.value.length} files.`);
    
    // Keep track of the original File objects to pass to the store
    const filesToProcess = [...uploadFiles.value];
    
    // Process files sequentially
    for (const file of filesToProcess) {
      const formData = new FormData();
      formData.append('file', file);

      // TODO: Make API URL configurable
      const apiUrl = 'http://localhost:8000/upload-and-extract'; 

      try {
        console.log(`[DocumentList] Uploading file: ${file.name}`);
        // Specify expected response type for axios
        const response = await axios.post<UploadedDocData>(apiUrl, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });

        console.log(`[DocumentList] Successfully uploaded ${file.name}. Backend response:`, response.data);
        
        // *** Call the new store action ***
        // Pass the data from backend and the original File object
        documentStore.addUploadedDocument(response.data, file); 

        // TODO: Add user feedback (e.g., Snackbar) for success
        // Example: showSnackbar(`Successfully uploaded ${file.name}`, 'success');

      } catch (error) {
        console.error(`[DocumentList] Failed to upload or process file ${file.name}:`, error.response?.data || error.message || error);
        // TODO: Show user-friendly error message
        // Example: showSnackbar(`Failed to upload ${file.name}: ${error.response?.data?.detail || error.message}`, 'error');
      }
    }
    
    console.log('[DocumentList] File upload process finished.');
    uploading.value = false;
  
  // --- DOI/URL Logic (Not implemented yet) ---
  } else if (uploadTab.value === 'doi' && doiInput.value) {
     console.warn('[DocumentList] DOI import not implemented yet.');
     // TODO: Implement DOI import logic (call backend endpoint if available)
  } else if (uploadTab.value === 'url' && urlInput.value) {
     console.warn('[DocumentList] URL import not implemented yet.');
     // TODO: Implement URL import logic (call backend endpoint if available)
  } else {
    console.warn('[DocumentList] No valid input for upload.');
    return; 
  }

  // --- Cleanup ---
  uploadFiles.value = []
  doiInput.value = ''
  urlInput.value = ''
  showUploadDialog.value = false
}

// 文档详情相关
const showDocDetails = (doc) => {
  detailDocument.value = doc
  showDocDetailsDialog.value = true
}

const editDocDetails = () => {
  // 实现编辑文档信息的逻辑
  console.log('编辑文档信息:', detailDocument.value.title)
  // 这里可以打开一个编辑表单对话框
}

const viewAndCloseDetails = () => {
  if (detailDocument.value) {
    selectDocument(detailDocument.value)
    showDocDetailsDialog.value = false
  }
}

// 工具方法
const formatDate = (dateString) => {
  if (!dateString) return '未知'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

const formatFileSize = (bytes) => {
  if (!bytes) return '未知'
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  
  return `${size.toFixed(1)} ${units[unitIndex]}`
}

// 初始化和监听
onMounted(async () => {
  loading.value = true
  try {
    // 确保有示例文档
    if (documentStore.documents.length === 0) {
      documentStore.addSampleDocuments()
    }
    
    // 如果有预选文档ID，则选择它
    if (props.selectedDocumentId) {
      const doc = documentStore.documents.find(d => d.id === props.selectedDocumentId)
      if (doc) {
        selectedDocument.value = doc
      }
    }
  } catch (error) {
    console.error('加载文档失败:', error)
  } finally {
    loading.value = false
  }
})

// 监听选中文档ID变化
watch(() => props.selectedDocumentId, (newId) => {
  if (newId && (!selectedDocument.value || selectedDocument.value.id !== newId)) {
    const doc = documentStore.documents.find(d => d.id === newId)
    if (doc) {
      selectedDocument.value = doc
    }
  }
})
</script>

<style scoped>
.document-list {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.list-header {
  padding: 12px 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
  background-color: white;
}

.search-upload-container {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.search-field {
  flex: 1;
}

.filter-tabs {
  margin-top: 4px;
}

.list-content {
  flex: 1;
  overflow-y: auto;
  background-color: #f5f5f5;
}

.document-items {
  background-color: white;
}

.document-list-item {
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  transition: background-color 0.2s, border-left 0.2s;
  position: relative;
}

.document-list-item:hover {
  background-color: rgba(0, 0, 0, 0.04);
  cursor: pointer;
}

.document-item-active {
  background-color: rgba(var(--v-theme-primary), 0.05) !important;
  border-left: 3px solid var(--v-theme-primary);
}

.document-actions {
  display: flex;
  align-items: center;
  opacity: 0.7;
}

.document-list-item:hover .document-actions {
  opacity: 1;
}

.filter-result {
  margin: 6px 0;
}

.loading-state, .empty-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 24px;
  color: rgba(0, 0, 0, 0.6);
}

.loading-text, .empty-text {
  margin-top: 16px;
  text-align: center;
}

/* 文档详情样式 */
.doc-details {
  padding: 8px;
}

.detail-item {
  margin-bottom: 16px;
}

.detail-label {
  font-weight: 500;
  color: rgba(0, 0, 0, 0.6);
  font-size: 0.9rem;
  margin-bottom: 4px;
}

.detail-value {
  color: rgba(0, 0, 0, 0.87);
}

.abstract-text {
  background-color: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  max-height: 200px;
  overflow-y: auto;
  font-style: italic;
  line-height: 1.5;
}
</style> 