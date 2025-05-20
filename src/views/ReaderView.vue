<template>
  <!-- 根容器，现在是行布局 -->
  <div class="reader-view-root" :class="{ 'focus-mode': focusMode }">
    <!-- 左侧面板容器 (可隐藏) -->
    <div 
      class="left-panels-container"
      :class="{ 'panels-hidden': !showLeftPanels }"
    >
      <!-- 上方：文献列表/导入 -->
      <div class="document-list-section">
        <document-list @select-document="onDocumentSelected" @handle-upload="handleUploadTrigger" :uploading="isUploading" />
      </div>
      
      <!-- 下方：知识面板 -->
      <div class="knowledge-panel-section">
        <v-card flat class="fill-height">
          <v-tabs v-model="activeTab" grow density="compact">
            <v-tab value="concepts" class="text-caption">概念</v-tab>
            <v-tab value="notes" class="text-caption">笔记</v-tab>
          </v-tabs>
          <v-divider></v-divider>
          <v-window v-model="activeTab" class="panel-content fill-height">
            <v-window-item value="concepts" class="concepts-panel">
              <!-- === REMOVE Section for Selected Concept === -->
              <!-- 
              <div v-if="selectedConcept" class="selected-concept-display pa-2 mb-2 elevation-1">
                 ... display logic ...
              </div>
              -->
               <div v-if="!currentDocumentMetadata" class="text-center pa-2 text-caption text-grey">
                 加载文献后将显示相关概念列表
              </div>
               <div v-else-if="!(currentDocumentMetadata.concepts && currentDocumentMetadata.concepts.length > 0)" class="text-center pa-2 text-caption text-grey">
                 当前文献未提取到概念
              </div>
               <div v-else class="text-caption text-grey pl-2 pt-1 mb-1" v-if="currentDocumentMetadata && currentDocumentMetadata.concepts && currentDocumentMetadata.concepts.length > 0">点击概念展开定义:</div>
              
              <!-- Use v-list with v-model:opened -->
              <div v-if="currentDocumentMetadata"> 
                <v-list 
                    v-if="currentDocumentMetadata.concepts && currentDocumentMetadata.concepts.length > 0" 
                    density="compact" 
                    v-model:opened="openedConceptGroups"
                 >
                  <v-list-group 
                    v-for="(concept, index) in currentDocumentMetadata.concepts" 
                    :key="index" 
                    :value="concept.term" 
                  >
                    <template v-slot:activator="{ props }">
                      <v-list-item 
                        v-bind="props" 
                        density="compact" 
                        class="concept-list-item"
                      >
                         <template v-slot:prepend>
                           <v-icon size="small" color="primary">mdi-lightbulb-outline</v-icon>
                           <v-icon size="x-small" class="ml-1">{{ openedConceptGroups.includes(concept.term) ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
                         </template>
                         <v-list-item-title class="text-caption">{{ concept.term }}</v-list-item-title>
                      </v-list-item>
                    </template>
                    
                    <v-list-item density="compact" class="concept-definition-item">
                      <v-list-item-content class="text-caption text-medium-emphasis pa-2 pl-6">
                         {{ conceptDefinitionsCache[concept.term] || '...' }}
                      </v-list-item-content>
                      <v-list-item-action class="pr-1">
                        <v-btn 
                          icon 
                          variant="text" 
                          size="x-small" 
                          title="在图谱中查看"
                          @click.stop="navigateToGraph(concept.term)"
                        >
                          <v-icon size="small">mdi-graph-outline</v-icon>
                        </v-btn>
                      </v-list-item-action>
                    </v-list-item>

                  </v-list-group>
                </v-list>
                 <div v-else class="text-center pa-2 text-caption text-grey">
                    当前文献未提取到概念
                 </div>
              </div>
               <div v-else class="text-center pa-2 text-caption text-grey">
                 加载文献后将显示相关概念列表
              </div>
            </v-window-item>
            <v-window-item value="notes">
              <div class="text-center pa-2">
                <div class="text-caption text-grey">暂无笔记</div>
                <v-btn color="primary" variant="text" class="mt-2" size="x-small">
                  <v-icon size="small" start>mdi-plus</v-icon>
                  添加笔记
                </v-btn>
              </div>
            </v-window-item>
          </v-window>
        </v-card>
      </div>
    </div>

    <!-- 右侧主阅读区域 -->
    <div class="reader-main-area" ref="readerMainAreaRef">
      <v-card class="reader-container" flat ref="readerCardRef">
        <v-card-title class="d-flex align-center reader-title">
          <div class="d-flex align-center">
            <!-- 左侧面板切换按钮 -->
            <v-btn
              icon
              variant="text"
              size="small"
              class="mr-2 toggle-left-panels-btn"
              @click="showLeftPanels = !showLeftPanels"
              title="切换侧边面板"
            >
              <v-icon>{{ showLeftPanels ? 'mdi-chevron-left' : 'mdi-chevron-right' }}</v-icon>
            </v-btn>
            <!-- 标题和芯片 -->
            文献阅读
            <v-chip size="x-small" color="primary" class="ml-2">预览版</v-chip>
          </div>
          <v-spacer></v-spacer>
          <!-- Display total pages only -->
          <span v-if="pages > 0" class="text-caption mr-4">共 {{ pages }} 页</span>
          <span v-else class="text-caption mr-4">共 - 页</span>
          <!-- 右侧控制按钮 -->
          <div class="d-flex align-center">
            <v-btn v-if="currentDocumentMetadata" icon class="mr-1" title="下载文献" size="small">
              <v-icon>mdi-download</v-icon>
            </v-btn>
            <v-btn v-if="currentDocumentMetadata" icon class="mr-1" title="收藏文献" size="small">
              <v-icon>mdi-star-outline</v-icon>
            </v-btn>
            <v-btn icon class="mr-1" title="专注模式" @click="toggleFocusMode" size="small">
              <v-icon>{{ focusMode ? 'mdi-fullscreen-exit' : 'mdi-fullscreen' }}</v-icon>
            </v-btn>
            <v-btn icon title="设置" size="small">
              <v-icon>mdi-cog</v-icon>
            </v-btn>
          </div>
        </v-card-title>
        
        <v-divider></v-divider>
        
        <!-- 内容滚动区域 -->
        <div class="reader-content-area pdf-viewer-container">
          <!-- Restore the v-for loop -->
          <div 
             v-if="pdf && currentDocumentMetadata && pages > 0" 
             class="pdf-wrapper-container" 
             @mouseup="handleTextSelection" 
             @touchend="handleTextSelection" 
           >
            <!-- PDF Viewer -->
            <div class="pdf-viewer">
            <VuePDF 
                v-for="pageNumber in pages" 
                :key="`${currentDocumentMetadata.id}-${pageNumber}`" 
                :pdf="pdf" 
                :page="pageNumber" 
                text-layer
                annotation-layer
                fit-parent
            />
            </div>

            <!-- Difficulty Heatmap Bar -->
            <div class="difficulty-bar">
              <div v-for="pageNumber in pages" :key="`diff-${pageNumber}`" class="difficulty-segment">
                <v-tooltip activator="parent" location="start" content-class="difficulty-tooltip">
                  <span v-if="getAggregatedPageDifficulty(pageNumber - 1) && getAggregatedPageDifficulty(pageNumber - 1).score > 0">
                    Page {{ pageNumber }}: Avg. Score {{ getAggregatedPageDifficulty(pageNumber - 1)?.score?.toFixed(3) }}
                    <div v-if="getAggregatedPageDifficulty(pageNumber - 1)?.reasonSummary" class="tooltip-reasons-summary mt-1">
                      {{ getAggregatedPageDifficulty(pageNumber - 1)?.reasonSummary }}
                    </div>
                    <div v-if="getAggregatedPageDifficulty(pageNumber - 1)?.segmentCountWithDifficulty > 0" class="text-caption mt-1">
                      ({{ getAggregatedPageDifficulty(pageNumber - 1)?.segmentCountWithDifficulty }} 个评分文本片段)
                    </div>
                  </span>
                  <span v-else>Page {{ pageNumber }}: Normal</span>
                </v-tooltip>
                <div 
                  class="segment-color" 
                  :style="{ backgroundColor: getDifficultyColor(getAggregatedPageDifficulty(pageNumber - 1)?.score) }"
                ></div>
              </div>
            </div>
          </div>
          <!-- End Restore -->
          
          <!-- Keep other states -->
           <div v-else-if="currentDocumentMetadata && !pdfSource" class="text-center my-12 pa-6 empty-state">
               <v-icon size="x-large" color="grey-lighten-1">mdi-cloud-upload-outline</v-icon>
               <div class="text-body-1 mt-4 text-grey">请上传此文献的 PDF 文件</div>
               <div class="text-caption text-grey">(当前会话未找到此文献的 PDF 数据)</div>
          </div>
          <div v-else-if="!currentDocumentMetadata" class="text-center my-12 pa-6 empty-state">
              <!-- Initial empty state (no document selected) -->
              <v-icon size="x-large" color="grey-lighten-1">mdi-file-document-outline</v-icon>
              <div class="text-h5 mt-4 text-grey-darken-1">尚未选择文献</div>
              <div class="text-body-1 mt-2 text-grey">请在左侧列表选择一篇文献，或上传新文献</div>
          </div>
        </div>

        <!-- Replace Tooltip with Menu -->
        <v-menu
          v-model="showMenu"
          :style="{ position: 'absolute', left: menuX + 'px', top: menuY + 'px' }" 
          location="bottom start"
          absolute
          :close-on-content-click="false"
          offset="0"
          max-width="300px"
          content-class="concept-menu-card" 
        >
          <v-card density="compact">
            <!-- Restore dynamic bindings -->
            <v-card-title class="text-subtitle-2 pa-2">{{ menuTerm }}</v-card-title>
            <v-divider></v-divider>
            <v-card-text class="text-caption pa-2">
              {{ menuDefinition }}
            </v-card-text>
            <v-divider></v-divider>
            <v-card-actions class="pa-1">
              <v-spacer></v-spacer>
              <v-btn 
                variant="text" 
                color="primary" 
                size="small" 
                @click="navigateToGraph(menuTerm)"
              >
                在图谱中查看
                <v-icon end size="small">mdi-graph-outline</v-icon>
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-menu>
        <!-- End Menu Component -->

      </v-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, shallowRef, nextTick } from 'vue'
import { useDocumentStore, type Document, type SegmentDifficultyMarker } from '@/stores/documents'
import DocumentList from '@/components/DocumentList.vue'
import { VuePDF, usePDF } from '@tato30/vue-pdf'
import '@tato30/vue-pdf/style.css'
import { useRouter } from 'vue-router'

// --- Add imports for lifecycle hooks ---
import { onUnmounted } from 'vue'

const documentStore = useDocumentStore()
const currentDocumentMetadata = computed(() => documentStore.currentDocument)
const router = useRouter()

const activeTab = ref('concepts')
const focusMode = ref(false)
const showLeftPanels = ref(true)
const isUploading = ref(false)

// --- Ref for the main reader area element ---
const readerMainAreaRef = ref<HTMLElement | null>(null);

// --- Use local cache for PDF data --- 
const pdfDataCache = ref<{ [key: string]: ArrayBuffer }>({});
// --- End local cache --- 

const pdfSource = shallowRef<string | ArrayBuffer | null>(null)
const { pdf, pages, info } = usePDF(pdfSource)

// --- State for Menu (previously Tooltip) --- 
const showMenu = ref(false); // Renamed from showTooltip
const menuTerm = ref('');     // Renamed
const menuDefinition = ref(''); // Renamed
const menuX = ref(0);        // Renamed
const menuY = ref(0);        // Renamed
// pdfWrapperRef no longer needed for position calculation
// --- End Menu State --- 

// --- State for Concept Panel Expansion --- 
const openedConceptGroups = ref<string[]>([])
const conceptDefinitionsCache = ref<{ [term: string]: string }>({});
// --- End Expansion State --- 

// --- Watcher for Caching Definitions --- 
watch(openedConceptGroups, async (newOpenGroups, oldOpenGroups) => {
    const newlyOpened = newOpenGroups.filter(term => !oldOpenGroups?.includes(term));
    if (newlyOpened.length > 0) {
        await ensureDefinitionsCached(newlyOpened);
    }
}, { deep: true });

// --- Function to ensure definitions are cached --- 
async function ensureDefinitionsCached(terms: string[]) {
    if (!currentDocumentMetadata.value?.concepts) return;
    const conceptsData = currentDocumentMetadata.value.concepts;

    for (const term of terms) {
        if (!conceptDefinitionsCache.value[term]) {
            const conceptData = conceptsData.find(c => c.term === term);
            if (conceptData?.definition) {
                conceptDefinitionsCache.value[term] = conceptData.definition;
            } else {
                conceptDefinitionsCache.value[term] = "（正在加载定义...）";
                try {
                    const response = await fetch(`/definition/${encodeURIComponent(term)}`);
                    if (response.ok) {
                        const data = await response.json();
                        const def = data.definition || "（暂无定义）";
                        conceptDefinitionsCache.value[term] = def;
                        updateConceptDefinitionInStore(term, def);
                    } else {
                        conceptDefinitionsCache.value[term] = "（获取定义失败）";
                    }
                } catch (e) {
                    conceptDefinitionsCache.value[term] = "（获取定义失败）";
                }
            }
        }
    }
}
// --- End Function --- 

onMounted(() => {
  // Clear cache on mount? Optional, depends if we want persistence across mounts
  // pdfDataCache.value = {}; 

  watch(() => documentStore.currentDocumentId, async (newId, oldId) => {
    console.log(`[Watcher Triggered] newId: ${newId}, oldId: ${oldId}`);
    if (newId && newId !== oldId) {
        console.log(`[Watcher] Calling loadPdfDataForDocument for ID: ${newId}`);
        await loadPdfDataForDocument(newId);
    } else if (!newId) {
        console.log(`[Watcher] Clearing PDF view because newId is null.`);
        pdfSource.value = null; 
    }
  }, { immediate: false });

  if (documentStore.currentDocumentId) {
      console.log(`[onMounted] Initial document ID found: ${documentStore.currentDocumentId}. Loading...`);
      loadPdfDataForDocument(documentStore.currentDocumentId);
  }

  // Ensure initial definitions are cached if needed
  if (openedConceptGroups.value.length > 0) {
       ensureDefinitionsCached(openedConceptGroups.value);
  }

  // --- Add/Remove event listener in lifecycle hooks ---
  document.addEventListener('fullscreenchange', handleFullscreenChange);
})

onUnmounted(() => {
  document.removeEventListener('fullscreenchange', handleFullscreenChange);
  // Clean up blob URLs if necessary
  Object.values(pdfDataCache.value).forEach(url => URL.revokeObjectURL(url)); 
})

// --- Revised toggleFocusMode function ---
function toggleFocusMode() {
  if (!readerMainAreaRef.value) return;

  if (!document.fullscreenElement) {
    // Enter fullscreen
    readerMainAreaRef.value.requestFullscreen()
      .then(() => {
        // focusMode state will be updated by the event listener
        console.log('Fullscreen requested successfully.');
      })
      .catch(err => {
        console.error(`Error attempting to enable full-screen mode: ${err.message} (${err.name})`);
        // Fallback: Just hide panels if fullscreen fails?
        // focusMode.value = true; // Or handle error differently
        // showLeftPanels.value = false;
      });
  } else {
    // Exit fullscreen
    if (document.exitFullscreen) {
      document.exitFullscreen()
        .then(() => {
          // focusMode state will be updated by the event listener
          console.log('Exited fullscreen successfully.');
        })
        .catch(err => {
          console.error(`Error attempting to disable full-screen mode: ${err.message} (${err.name})`);
        });
    }
  }
}

// --- Function to handle fullscreen change events ---
function handleFullscreenChange() {
  if (document.fullscreenElement === readerMainAreaRef.value) {
    focusMode.value = true;
    showLeftPanels.value = false; // Ensure panels are hidden
    console.log('Entered fullscreen mode for reader area.');
  } else {
    focusMode.value = false;
    showLeftPanels.value = true; // Ensure panels are shown when exiting
    console.log('Exited fullscreen mode or fullscreen element changed.');
  }
}

function highlightParagraph(index) {
  // Implementation needed
}

const onDocumentSelected = (doc: Document | { id: string }) => {
  if (doc && doc.id) {
      console.log(`[onDocumentSelected] Selecting document ID: ${doc.id}`);
      if (documentStore.currentDocumentId !== doc.id) {
          documentStore.setCurrentDocument(doc.id);
      } else {
          console.log(`[onDocumentSelected] Document ID ${doc.id} already selected.`);
      }
  } else {
      console.warn('[onDocumentSelected] Invalid document object received:', doc);
  }
}

const handleUploadTrigger = (payload) => {
  console.log('[ReaderView] Received handle-upload event:', payload);
  if (payload.type === 'file') {
    processUploadedFiles(payload.files);
  } else {
    console.warn(`[ReaderView] Import type '${payload.type}' not yet implemented.`);
  }
}

async function processUploadedFiles(uploadedFiles: File[]) {
  if (!uploadedFiles || uploadedFiles.length === 0) {
    console.warn('[processUploadedFiles] No files received.');
    return;
  }
  isUploading.value = true;

  try {
    for (const file of uploadedFiles) {
      console.log(`[processUploadedFiles] 开始处理文件: ${file.name}`);
      // Remove existing doc with same name if needed
      const existingDocIndex = documentStore.documents.findIndex(d => d.fileName === file.name);
      if (existingDocIndex > -1) {
          const existingDocId = documentStore.documents[existingDocIndex].id;
          console.warn(`[processUploadedFiles] 发现同名文档 (ID: ${existingDocId})，正在移除...`);
          documentStore.removeDocument(existingDocId);
          // Also remove from local cache if it exists
          if (pdfDataCache.value[existingDocId]) {
              delete pdfDataCache.value[existingDocId];
              console.log(`[processUploadedFiles] Removed existing PDF data from cache for ID: ${existingDocId}`);
          }
      }

      let fileBuffer: ArrayBuffer | null = null;
      try {
        fileBuffer = await readFileAsArrayBuffer(file);
        console.log(`[processUploadedFiles] 文件读取完成: ${file.name}, 大小: ${fileBuffer?.byteLength}`);
      } catch (readError) {
        console.error(`[processUploadedFiles] 读取文件失败: ${file.name}`, readError);
        continue;
      }
      // Ensure fileBuffer is valid before proceeding
      if (!fileBuffer || fileBuffer.byteLength === 0) { 
          console.error(`[processUploadedFiles] 读取到的 ArrayBuffer 无效 for file: ${file.name}`);
          continue;
      }

      let titleFromFile = file.name.replace(/\.pdf$/i, "").replace(/_/g, ' ');
      const newDocMetadata: Document = {
        id: Date.now() + Math.random().toString(36).substr(2, 9),
        title: titleFromFile || "未知标题",
        authors: ['未知作者'],
        year: new Date().getFullYear().toString(),
        abstract: '摘要待提取',
        content: [],
        fileName: file.name,
        fileType: file.type,
        fileSize: file.size,
        uploadDate: new Date(),
        lastReadDate: new Date(),
        tags: [],
        concepts: [],
        relationships: [], // Initialize relationships
        difficulty_markers: [], // Initialize difficulty_markers
        // No pdfData field here anymore
      };

      console.log(`[processUploadedFiles] 准备添加元数据文档 (ID: ${newDocMetadata.id}) 到 Store`);
      documentStore.addDocument(newDocMetadata);
      console.log(`[processUploadedFiles] 元数据文档已添加到 Store (ID: ${newDocMetadata.id})`);

      // --- Store a CLONE of PDF data in local cache --- 
      console.log(`[processUploadedFiles] 准备将 ArrayBuffer (size: ${fileBuffer.byteLength}) 的克隆存储到本地缓存 for ID: ${newDocMetadata.id}`);
      try {
          const clonedBuffer = fileBuffer.slice(0); // Create a clone
          pdfDataCache.value[newDocMetadata.id] = clonedBuffer;
          // Log size immediately after storing the clone
          console.log(`[processUploadedFiles] 克隆的 ArrayBuffer 已存储到本地缓存 for ID: ${newDocMetadata.id}. Cached size: ${pdfDataCache.value[newDocMetadata.id]?.byteLength}`);
      } catch (cloneError) {
          console.error(`[processUploadedFiles] 克隆或存储 ArrayBuffer 到缓存时出错 for ID: ${newDocMetadata.id}`, cloneError);
          // Optionally skip setting current doc if caching fails
          continue; 
      }
      // --- End storing clone in cache --- 

      console.log(`[processUploadedFiles] 准备设置当前文档 ID: ${newDocMetadata.id}`);
      documentStore.setCurrentDocument(newDocMetadata.id); 
    }
    console.log('[processUploadedFiles] 所有文件处理完毕');
  } catch (error) {
    console.error('[processUploadedFiles] 顶层捕获错误:', error);
  } finally {
    isUploading.value = false;
    console.log('[processUploadedFiles] 执行结束 (finally)');
  }
}

async function loadPdfDataForDocument(docId: string) {
    console.log(`[loadPdfData] Function Start. Attempting to load ID: ${docId}`);
    const docMetadata = documentStore.documents.find(d => d.id === docId);
    if (!docMetadata) {
        console.error(`[loadPdfData] Metadata NOT FOUND for ID: ${docId}`);
        pdfSource.value = null; 
        return;
    }
    console.log(`[loadPdfData] Metadata FOUND for ID: ${docId}, Title: ${docMetadata.title}`);
    
    // *** Prioritize Blob URL for uploaded documents ***
    if (docMetadata.blobUrl) {
        console.log(`[loadPdfData] Blob URL FOUND for ID: ${docId}. Setting pdfSource.`);
        if (pdfSource.value !== docMetadata.blobUrl) {
             pdfSource.value = docMetadata.blobUrl; 
             console.log(`[loadPdfData] pdfSource UPDATED with Blob URL: ${docMetadata.blobUrl}`);
        } else {
             console.log(`[loadPdfData] pdfSource already holds the same Blob URL.`);
        }
        return; // Stop here if blobUrl is used
    }
    
    console.log(`[loadPdfData] Blob URL not found for ID: ${docId}. Falling back to local cache.`);

    // --- Load PDF data from local cache (Keep as fallback for now) --- 
    try {
        // Log the entire cache object before accessing
        console.log('[loadPdfData] Inspecting pdfDataCache before access:', pdfDataCache.value);

        const cachedData = pdfDataCache.value[docId];
        console.log(`[loadPdfData] Accessed cache for ID: ${docId}. Found data object:`, cachedData);

        if (cachedData && cachedData.byteLength > 0) { 
            console.log(`[loadPdfData] Valid PDF data FOUND in local cache for ID: ${docId}. Size: ${cachedData.byteLength}. Preparing clone for pdfSource.`);
            
            try {
                const clonedDataForSource = cachedData.slice(0); // Create another clone for pdfSource
                console.log(`[loadPdfData] Successfully cloned cached data for pdfSource. Clone size: ${clonedDataForSource.byteLength}`);

                // Check if source is already this ArrayBuffer to avoid redundant updates
                // Simple comparison might not work perfectly for ArrayBuffers, but worth a try
                if (pdfSource.value !== clonedDataForSource) { 
                     pdfSource.value = clonedDataForSource; 
                     console.log(`[loadPdfData] pdfSource UPDATED with CLONE from cache for ID: ${docId}. usePDF should load.`);
                } else {
                     console.log(`[loadPdfData] pdfSource already holds the exact same cloned data object for ID (${docId}). Skipping update.`);
                }
            } catch (sourceCloneError) {
                console.error(`[loadPdfData] Error cloning cached ArrayBuffer for pdfSource (ID: ${docId}):`, sourceCloneError);
                if (pdfSource.value !== null) pdfSource.value = null;
            }
        } else {
            console.warn(`[loadPdfData] PDF data NOT FOUND or invalid (Size: ${cachedData?.byteLength}) in local cache for ID: ${docId}. Clearing pdfSource.`);
            if (pdfSource.value !== null) { 
                pdfSource.value = null;
            }
        }
    } catch (error) {
        console.error(`[loadPdfData] ERROR accessing local cache or setting pdfSource for ID ${docId}:`, error);
        if (pdfSource.value !== null) {
            pdfSource.value = null;
        }
    }
}

function readFileAsArrayBuffer(file: File): Promise<ArrayBuffer> {
  console.log('[readFileAsArrayBuffer] 开始读取', file.name);
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      console.log('[readFileAsArrayBuffer] 读取成功', file.name);
      resolve(reader.result as ArrayBuffer);
    }
    reader.onerror = (error) => {
      console.error('[readFileAsArrayBuffer] 读取错误', file.name, error);
      reject(error);
    }
    reader.readAsArrayBuffer(file);
  });
}

// --- Modified Text Selection Handler --- 
function handleTextSelection() {
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0) {
        hideMenu(); // Use hideMenu
        return; 
    }

    const selectedText = selection.toString().trim();
    console.log("[handleTextSelection] Selected text:", selectedText);

    if (selectedText && currentDocumentMetadata.value && currentDocumentMetadata.value.concepts) {
        const concepts = currentDocumentMetadata.value.concepts; 
        const foundConcept = concepts.find(concept => 
            concept.term.toLowerCase() === selectedText.toLowerCase()
        );

        if (foundConcept) {
            console.log("[handleTextSelection] Found matching concept term:", foundConcept.term);
            showConceptMenu(foundConcept, selection.getRangeAt(0).getBoundingClientRect()); // Use showConceptMenu
        } else {
            console.log("[handleTextSelection] No matching concept found in list.");
            hideMenu(); 
        }
    } else {
         hideMenu(); 
    }
}
// --- End Text Selection Handler --- 

// --- Menu/Popup Functions --- 
async function showConceptMenu(concept: { term: string, definition: string }, rect: DOMRect) {
    hideMenu(); 
    await nextTick(); 

    menuX.value = rect.left;
    menuY.value = rect.bottom + 5;
    menuTerm.value = concept.term;

    let def = conceptDefinitionsCache.value[concept.term] || concept.definition || "（正在加载定义...）";
    menuDefinition.value = def;
    showMenu.value = true; 

    if (!conceptDefinitionsCache.value[concept.term] || conceptDefinitionsCache.value[concept.term] === "（正在加载定义...）") {
        try {
            const response = await fetch(`/definition/${encodeURIComponent(concept.term)}`);
            if (response.ok) {
                const data = await response.json();
                def = data.definition || "（暂无定义）";
                conceptDefinitionsCache.value[concept.term] = def;
                menuDefinition.value = def;
                updateConceptDefinitionInStore(concept.term, def);
            } else {
                menuDefinition.value = "（获取定义失败）";
            }
        } catch (e) {
            menuDefinition.value = "（获取定义失败）";
        }
    }
}

function hideMenu() {
    if (showMenu.value) {
      console.log("[hideMenu] Hiding menu");
      showMenu.value = false;
    }
}

// --- Function to navigate to graph view --- 
function navigateToGraph(term: string) {
  if (!term) {
    console.warn("[ReaderView] navigateToGraph called with no term.");
    return;
  }

  console.log(`[ReaderView] Attempting to navigate to graph for term: ${term}`);
  try {
    // Assuming setConceptToHighlight is correctly implemented in the store
    if (documentStore.setConceptToHighlight) {
        documentStore.setConceptToHighlight(term);
        console.log(`[ReaderView] Called setConceptToHighlight for: ${term}`);
    } else {
        console.warn("[ReaderView] documentStore.setConceptToHighlight is not defined!");
        // Decide if you want to navigate even if highlighting fails
        // For now, we'll still try to navigate.
    }
  } catch (error) {
    console.error(`[ReaderView] Error calling setConceptToHighlight for ${term}:`, error);
    // Optionally, decide if navigation should be aborted on error
  }

  // Attempt navigation regardless of highlight setting outcome (unless critical error above)
  try {
    router.push('/knowledge-graph');
    console.log("[ReaderView] router.push('/knowledge-graph') called.");
    hideMenu(); // Close menu if open
  } catch (navError) {
    console.error("[ReaderView] Error during router.push('/knowledge-graph'):", navError);
    }
}
// --- End Menu/Popup Functions --- 

// --- Difficulty Bar Helper Functions (MODIFIED) ---
interface AggregatedPageDifficulty {
  score: number;
  uniqueReasons: Array<{ reason: string; count: number }>;
  segmentCountWithDifficulty: number;
  reasonSummary: string;
}

const reasonKeyToSummaryLabel: { [key: string]: string } = {
  'term_density_segment': '术语',
  'formulas_in_segment': '公式',
  'figures_on_page': '图表',
  'tables_on_page': '表格',
  'citations_in_segment': '引用',
  'long_sentences_in_segment': '长难句'
};

function getAggregatedPageDifficulty(pageIndex: number): AggregatedPageDifficulty | null {
  if (!currentDocumentMetadata.value?.difficulty_markers) {
    return null;
  }

  const markersForPage = currentDocumentMetadata.value.difficulty_markers.filter(
    (marker: SegmentDifficultyMarker) => marker.page_index === pageIndex && marker.score > 0
  );

  if (markersForPage.length === 0) {
    return { score: 0, uniqueReasons: [], segmentCountWithDifficulty: 0, reasonSummary: "" };
  }

  const totalScore = markersForPage.reduce((sum, marker) => sum + marker.score, 0);
  const averageScore = parseFloat((totalScore / markersForPage.length).toFixed(3));
  
  const reasonCounts: { [key: string]: number } = {};
  const baseReasonTypesForSummary = new Set<string>();

  markersForPage.forEach(marker => {
    marker.reasons.forEach(rawReasonString => {
      reasonCounts[rawReasonString] = (reasonCounts[rawReasonString] || 0) + 1;
      const key = rawReasonString.split(' ')[0]; // Extracts "term_density_segment" from "term_density_segment (5)"
      if (reasonKeyToSummaryLabel[key]) {
        baseReasonTypesForSummary.add(reasonKeyToSummaryLabel[key]);
      }
    });
  });

  const uniqueReasonsForDetail = Object.entries(reasonCounts)
    .map(([reason, count]) => ({ reason, count }))
    .sort((a, b) => b.count - a.count);

  let reasonSummaryText = "";
  if (baseReasonTypesForSummary.size > 0) {
    const sortedTypes = Array.from(baseReasonTypesForSummary);
    if (sortedTypes.length === 1) {
        reasonSummaryText = `主要由于存在${sortedTypes[0]}。`;
    } else if (sortedTypes.length === 2) {
        reasonSummaryText = `主要由于存在${sortedTypes[0]}及${sortedTypes[1]}。`;
    } else if (sortedTypes.length > 2) {
        const firstFew = sortedTypes.slice(0, 2);
        reasonSummaryText = `主要由于存在${firstFew.join('、')}及${sortedTypes[sortedTypes.length-1]}等因素。`;
    } else { // Should not happen if size > 0
        reasonSummaryText = "涉及多种复杂因素。";
    }
  } else if (averageScore > 0) { 
      reasonSummaryText = "综合因素导致一定难度。";
  }
  return {
    score: averageScore,
    uniqueReasons: uniqueReasonsForDetail, // Still available if needed for a more detailed view
    segmentCountWithDifficulty: markersForPage.length,
    reasonSummary: reasonSummaryText
  };
}


function getDifficultyColor(score?: number): string {
  if (typeof score === 'undefined' || score === null || score <= 0) return 'rgba(0, 128, 0, 0.1)'; // Light green for normal/no score or low avg
  // Adjust thresholds for average scores if needed
  if (score <= 0.1) return 'rgba(173, 216, 230, 0.3)'; // Lighter blue for very low scores (e.g. 0.001 to 0.1)
  if (score <= 0.3) return 'rgba(173, 216, 230, 0.5)'; // Light blue for low scores (e.g. 0.101 to 0.3)
  if (score <= 0.5) return 'rgba(255, 255, 0, 0.5)'; // Yellow for medium-low (e.g. 0.301 to 0.5)
  if (score <= 0.7) return 'rgba(255, 165, 0, 0.6)'; // Orange for medium-high (e.g. 0.501 to 0.7)
  if (score > 0.7) return 'rgba(255, 0, 0, 0.7)';   // Red for high (e.g. > 0.7)
  return 'rgba(128, 128, 128, 0.2)'; // Default grey for unexpected scores
}

function formatReason(reason: string): string {
  const reasonMap: { [key: string]: string } = {
    'high_term_density': '术语密度较高', // Kept for potential future page-level summary
    'high_term_density_segment': '术语密度 (片段)',
    'formulas_present': '包含公式/符号', // Kept
    'formulas_in_segment': '公式/符号 (片段)',
    'citations_present': '包含较多引用', // Kept
    'citations_in_segment': '较多引用 (片段)',
    'long_sentences_in_segment': '长难句 (片段)',
    'figures_on_page': '含图表 (页面)',
    'tables_on_page': '含表格 (页面)'
  };
  // Handle reasons like "long_sentences_in_segment (3)"
  const match = reason.match(/^(.*?)\s*\((\d+)\)$/);
  if (match) {
    const baseReason = match[1];
    const count = match[2];
    return `${reasonMap[baseReason] || baseReason.replace(/_/g, ' ')} (${count})`;
  }
  return reasonMap[reason] || reason.replace(/_/g, ' ');
}
// --- End Difficulty Bar Helper Functions ---

// Placeholder function for popup remains
function showConceptPopup(term: string, rect: DOMRect) {
    console.log(`[Placeholder] Triggered showConceptPopup for term: '${term}' at position:`, rect);
}

async function fetchAndShowDefinition(term: string) {
  // 1. (Optional) Show loading state in your explanation window
  
  try {
    const response = await fetch(`/definition/${encodeURIComponent(term)}`); // 注意你的API路径，可能是/api/definition或直接/definition
    if (!response.ok) {
      throw new Error(`Failed to fetch definition for ${term}`);
    }
    const data = await response.json(); // Expects { term: string, definition: string | null }
    
    // 2. Display data.definition in your explanation window
    // 3. Update Pinia store (see section 3 below)
    updateConceptDefinitionInStore(term, data.definition);

  } catch (error) {
    console.error("Error fetching definition:", error);
    // 4. Show error state in your explanation window
  } finally {
    // 5. (Optional) Hide loading state
  }
}

async function onSidebarConceptClick(conceptTerm: string) {
  const currentDoc = documentStore.currentDocument;
  if (!currentDoc) return;

  const conceptInStore = currentDoc.concepts.find(c => c.term === conceptTerm);

  // 1. Check if definition is already cached in store
  if (conceptInStore && conceptInStore.definition !== null && conceptInStore.definition !== undefined) {
    // Display conceptInStore.definition in your explanation window or a dedicated area
    // For example, you might call a global function to show the explanation window:
    // showGlobalExplanationWindow(conceptTerm, conceptInStore.definition);
    console.log(`Using cached definition for ${conceptTerm}: ${conceptInStore.definition}`);
    return;
  }

  // 2. If not cached, fetch it (you can reuse the fetchAndShowDefinition logic)
  //    This function should also handle displaying it and updating the store.
  await fetchAndShowDefinition(conceptTerm); 
}

// Helper function to be called within fetchAndShowDefinition or after API call
function updateConceptDefinitionInStore(termToUpdate: string, newDefinition: string | null) {
  const doc = documentStore.currentDocument;
  if (doc) {
    const conceptIndex = doc.concepts.findIndex(c => c.term === termToUpdate);
    if (conceptIndex !== -1) {
      // Create a new concepts array for reactivity if not using Immer or similar deeply reactive solution for arrays
      const updatedConcepts = [...doc.concepts]; 
      updatedConcepts[conceptIndex] = {
        ...updatedConcepts[conceptIndex],
        definition: newDefinition
      };
      // Call your existing updateDocument action from the store
      documentStore.updateDocument(doc.id, { concepts: updatedConcepts }); 
      console.log(`Updated definition for ${termToUpdate} in store.`);
    }
  }
}

</script>

<style scoped>
.reader-view-root {
  height: 100%;
  display: flex;
  overflow: auto;
}

.left-panels-container {
  width: 300px;
  height: 100%;
  display: flex;
  flex-direction: column;
  border-right: 1px solid rgba(0, 0, 0, 0.12);
  transition: width 0.3s ease;
  overflow: auto;
  flex-shrink: 0;
  background-color: #f8f9fa;
  box-shadow: 1px 0 3px rgba(0, 0, 0, 0.05);
}

.left-panels-container.panels-hidden {
  width: 0;
  border: none;
  padding: 0;
  margin: 0;
  box-shadow: none;
  overflow: hidden;
  transition: width 0.3s ease;
}

.document-list-section {
  flex: 3 1 30%;
  min-height: 280px;
  overflow: auto;
  display: flex;
  flex-direction: column;
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
}

.knowledge-panel-section {
  flex: 2 1 25%;
  overflow: auto;
  display: flex;
  flex-direction: column;
}

.reader-main-area {
  flex: 1 1 auto;
  width: 1110px;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: auto;
  background-color: white;
  min-width: 0;
}

.reader-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
}

.reader-title {
  padding: 10px 24px;
  background-color: white;
  flex-shrink: 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
}

.toggle-left-panels-btn {
  margin-right: 10px;
  color: rgba(0, 0, 0, 0.7);
  min-width: 36px;
  height: 36px;
  border-radius: 4px;
}

.toggle-left-panels-btn:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.reader-content-area {
  flex: 1;
  overflow-y: auto;
  padding: 10px 5px;
  scroll-behavior: smooth;
  width: 100%;
}

.pdf-viewer-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  padding: 0;
  width: 100%;
}

.pdf-wrapper-container {
  display: flex;
  flex-direction: row;
  position: relative;
  flex-grow: 1;
  overflow: hidden;
  width: 100%;
}

.pdf-viewer {
  flex-grow: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 10px;
  background-color: #f0f0f0;
}

.difficulty-bar {
  width: 6px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: #e0e0e0;
  flex-shrink: 0;
  box-shadow: -1px 0 3px rgba(0,0,0,0.1);
  overflow: hidden;
}

.difficulty-segment {
  flex-grow: 1;
  min-height: 5px;
  width: 100%;
  position: relative;
  cursor: help;
  border-bottom: 1px solid rgba(0,0,0,0.05);
  display: flex;
}

.segment-color {
  width: 100%;
  height: 100%;
  transition: background-color 0.3s ease;
}

.difficulty-segment:hover .segment-color {
  filter: brightness(1.1);
}

:deep(.difficulty-tooltip) {
  background-color: rgba(50, 50, 50, 0.95) !important; /* Darker for better contrast */
  color: white !important;
  font-size: 0.75rem !important;
  padding: 6px 10px !important; /* Slightly more padding */
  border-radius: 4px !important;
  max-width: 250px; /* Prevent overly wide tooltips */
  pointer-events: none; /* Allow interaction with elements below if needed */
}

.tooltip-reasons-summary {
  font-size: 0.7rem; /* Smaller font for reason summary */
}

.tooltip-reasons {
  padding-left: 15px;
  margin-top: 2px;
  margin-bottom: 0;
  list-style-type: disc;
  font-size: 0.7rem; /* Smaller font for reason list items */
}

.metadata-display {
    overflow-y: auto;
}

.document-header {
  margin-bottom: 10px;
  max-width: 90%;
  margin-left: auto;
  margin-right: auto;
}

.document-meta {
  color: rgba(0, 0, 0, 0.6);
  margin-bottom: 10px;
}

.authors { margin-bottom: 4px; }
.publication-info { margin-bottom: 8px; font-style: italic; }
.tags { display: flex; flex-wrap: wrap; margin-top: 8px; }
.abstract {
  background-color: rgba(0, 0, 0, 0.02);
  padding: 2px;
  border-radius: 6px;
  margin-bottom: 32px;
  max-width: 100%;
  border-left: 4px solid rgba(var(--v-theme-primary), 0.5);
}
.abstract h3 { font-size: 1.2rem; margin-bottom: 12px; color: rgba(0, 0, 0, 0.7); }
.empty-state { 
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: rgba(0, 0, 0, 0.5);
  height: 100%;
}
.reader-content-area::-webkit-scrollbar {
  width: 10px;
}
.reader-content-area::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 6px;
}
.reader-content-area::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 6px;
}
.reader-content-area::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.4);
}
.reader-view-root.focus-mode .pdf-wrapper-container {
    padding: 0;
    background-color: #525252;
}
.reader-view-root.focus-mode .metadata-display {
    display: none;
}
@media (min-width: 180px) {
  .metadata-display .document-header { max-width: 85%; }
  .metadata-display .abstract { max-width: 85%; margin-left: auto; margin-right: auto; }
}

:deep(.vue-pdf-container) {
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
}

:deep(.vue-pdf-page) { 
  margin-bottom: 15px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

:deep(.textLayer) ::selection {
  background: rgba(0, 100, 255, 0.3);
}

/* Add pointer cursor to clickable list items */
.concepts-panel .v-list-item--link {
  cursor: pointer;
}

.concepts-panel .v-list-item:hover {
  background-color: rgba(0,0,0,0.05);
}

/* Style for the menu card */
.concept-menu-card .v-card {
  background-color: rgba(40, 40, 40, 0.95); 
  color: white; 
  border-radius: 4px;
  pointer-events: auto; 
  min-width: 100px ;
  min-height: 50px ;
  border: 1px solid black ;
  z-index: 9999 ;
}

.concept-menu-card .v-card-title,
.concept-menu-card .v-card-text {
  color: black; 
  padding: 7px;
  display: block; 
}

.concept-list-item .v-list-item-title {
  margin-left: 4px; /* Add some space after icons */
}

.concept-definition-item {
   background-color: rgba(0,0,0,0.03);
   border-left: 3px solid rgba(var(--v-theme-primary), 0.3);
   margin-bottom: 2px; /* Add space below definition */
}

/* Style v-list-group header to remove default padding/min-height issues if needed */
:deep(.v-list-group__header.v-list-item) {
  padding-inline-start: 16px !important; /* Adjust default padding */
  min-height: 32px !important; /* Adjust default min-height */
}

/* Ensure concepts-panel allows scrolling */
.concepts-panel {
  overflow-y: auto;
  height: 100%; 
}

/* Hide scrollbar on the knowledge panel itself if inner scrolling works */
.knowledge-panel-section {
  /* overflow: hidden; */ /* Might hide scrollbar if panel scrolls */
}

/* When in focus mode */
.reader-view-root.focus-mode {
  /* Optionally override root background if needed, e.g., for a darker theme */
  /* background-color: #212121; */
}

/* Hide the reader's internal header in focus mode */
.reader-view-root.focus-mode .reader-title {
  display: none;
}

/* Remove content area padding when header is hidden in focus mode */
.reader-view-root.focus-mode .reader-content-area {
  padding: 0;
}

/* Adjust pdf wrapper padding/background for focus mode */
.reader-view-root.focus-mode .pdf-wrapper-container {
  padding: 0; /* Remove padding for edge-to-edge */
  background-color: #525252; /* Darker background for focus */
}

/* Remove focus mode specific styles for metadata-display as it's not used */
/* 
.reader-view-root.focus-mode .metadata-display {
    display: none;
} 
*/

</style>