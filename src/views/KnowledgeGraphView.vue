<template>
  <div class="knowledge-graph-view fill-height d-flex flex-column">
    <v-toolbar density="compact" flat class="flex-grow-0">
      <v-toolbar-title class="d-flex align-center">
        知识图谱
        <v-chip small color="primary" variant="tonal" class="ml-2">ECharts</v-chip>
      </v-toolbar-title>
            <v-spacer></v-spacer>
            <v-select
              v-model="selectedView"
              :items="viewOptions"
        label="视图类型"
              hide-details
        variant="outlined"
              density="compact"
        class="mr-3"
        style="max-width: 200px;"
            ></v-select>
      <v-btn icon class="mr-2" title="切换全屏" @click="toggleFullScreen">
        <v-icon>{{ isFullScreen ? 'mdi-fullscreen-exit' : 'mdi-fullscreen' }}</v-icon>
            </v-btn>
      <v-btn icon title="图谱设置" @click="controlsDrawer = !controlsDrawer">
              <v-icon>mdi-cog</v-icon>
            </v-btn>
    </v-toolbar>
          
          <v-divider></v-divider>
          
    <div class="d-flex flex-grow-1" style="position: relative; overflow: hidden;">
            <!-- 图谱可视化区域 -->
      <div class="graph-main-content flex-grow-1" ref="graphWrapperRef">
        <div v-if="isLoading" class="fill-height d-flex justify-center align-center flex-column">
          <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
          <div class="text-body-1 mt-4 text-grey-darken-1">正在加载图谱...</div>
        </div>
        <div v-else-if="!processedGraphData || processedGraphData.nodes.length === 0" class="fill-height d-flex justify-center align-center flex-column">
          <v-icon size="96" color="grey-lighten-1">mdi-graph-outline</v-icon>
          <div class="text-h5 mt-6 text-grey-darken-1">暂无知识图谱数据</div>
          <div class="text-body-1 mt-2 text-grey">当前文献没有可供展示的概念关系。</div>
          <v-btn color="primary" class="mt-8" to="/reader" prepend-icon="mdi-book-open-variant">
            选择或上传文献
                  </v-btn>
                </div>
        <!-- ECharts 容器 -->
        <div v-show="filteredGraphData && filteredGraphData.nodes.length > 0" ref="echartsContainerRef" class="echarts-graph-container"></div>
              </div>

      <!-- 控制面板抽屉 -->
      <v-navigation-drawer
        v-model="controlsDrawer"
        location="right"
        temporary
        width="320"
        class="control-panel-drawer"
      >
        <v-list-item title="图谱控制" subtitle="调整图谱展示效果"></v-list-item>
              <v-divider></v-divider>
              
              <div class="pa-4">
                <v-text-field
                  label="搜索节点"
                  variant="outlined"
                  density="compact"
                  prepend-inner-icon="mdi-magnify"
                  hide-details
                  class="mb-4"
            v-model="searchTerm"
            clearable
                ></v-text-field>
                
          <v-list-subheader>过滤选项</v-list-subheader>
                <v-checkbox
                  v-for="(filter, index) in filters"
                  :key="index"
                  v-model="filter.value"
                  :label="filter.label"
                  hide-details
                  density="compact"
            class="my-n1"
                ></v-checkbox>
                
          <v-list-subheader class="mt-4">布局控制</v-list-subheader>
          <div class="px-1">
                <v-slider
                  v-model="layoutControls.nodeDistance"
              label="节点斥力"
                  :min="10"
              :max="500" 
              thumb-label="always"
              class="my-2"
              @update:model-value="throttledDrawGraph"
              hide-details
                ></v-slider>
                <v-slider
              v-model="layoutControls.linkLength"
              label="连接长度"
              :min="10"
              :max="300"
              thumb-label="always"
              class="my-2"
              @update:model-value="throttledDrawGraph"
              hide-details
                ></v-slider>
                 <v-slider 
                    v-model="layoutControls.gravityToCategory"
                    label="类别向心力"
                  :min="0"
                    :max="1"
                    :step="0.01"
                    thumb-label="always"
                    class="my-2"
                    @update:model-value="throttledDrawGraph"
                    hide-details
                ></v-slider>
          </div>
                
          <v-btn block color="primary" variant="tonal" class="mt-6" prepend-icon="mdi-export">
                  导出图谱
                </v-btn>
              </div>
      </v-navigation-drawer>
    </div>
  </div>
  <v-snackbar v-model="snackbar.visible" :color="snackbar.color" timeout="3000">
    {{ snackbar.message }}
    <template #actions>
      <v-btn icon @click="snackbar.visible = false">
        <v-icon>mdi-close</v-icon>
      </v-btn>
    </template>
  </v-snackbar>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import { useDocumentStore } from '@/stores/documents';
import { storeToRefs } from 'pinia';
import * as echarts from 'echarts/core';
import { GraphChart, GraphSeriesOption } from 'echarts/charts';
import { TitleComponent, TooltipComponent, LegendComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import type { EChartsOption, EChartsType } from 'echarts/core';
import { throttle } from 'lodash-es';

echarts.use([
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GraphChart,
  CanvasRenderer
]);

// --- Interfaces for global graph data (matching backend Pydantic models) ---
interface GlobalGraphNode {
  id: string; // Concept term
  name: string; // Concept term
  document_ids: string[];
  category_index?: number; // Will be used by ECharts
  // ECharts specific properties that can be added directly to nodes
  symbolSize?: number;
  itemStyle?: { color?: string }; 
  label?: { show?: boolean; fontSize?: number; };
}

interface GlobalGraphLink {
  source: string; // Source concept term
  target: string; // Target concept term
  label?: string;
  document_id: string; // The document this link was primarily extracted from
  lineStyle?: { opacity?: number; width?: number; type?: string; color?: string; curveness?: number };
}

interface GlobalGraphDocument {
  id: string;
  title: string;
}

interface GlobalGraphData {
  nodes: GlobalGraphNode[];
  links: GlobalGraphLink[];
  documents: GlobalGraphDocument[]; // For category names
}
// --- End Interfaces ---

const snackbar = ref({
  visible: false,
  message: '',
  color: 'info'
});

const selectedView = ref('概念网络'); // For now, always global concept network
const viewOptions = ['概念网络', '文献关系图', '作者合作网络'];
const searchTerm = ref('');
const isLoading = ref(false);
const controlsDrawer = ref(true);

const documentStore = useDocumentStore();
const { conceptToHighlightInGraph } = storeToRefs(documentStore); // currentDocument no longer primary source

const echartsContainerRef = ref<HTMLElement | null>(null);
const graphWrapperRef = ref<HTMLElement | null>(null);
let chartInstance: EChartsType | null = null;
const isFullScreen = ref(false);

// --- State for fetched global graph data ---
const rawGlobalGraphData = ref<GlobalGraphData | null>(null);
// --- End State ---

// --- Computed property to process rawGlobalGraphData for ECharts ---
const processedGraphData = computed(() => {
  if (!rawGlobalGraphData.value) {
    return { nodes: [], links: [], categories: [] };
  }

  const { nodes: rawNodes, links: rawLinks, documents } = rawGlobalGraphData.value;

  const categories = documents.map(doc => ({ name: doc.title || doc.id }));

  const nodes = rawNodes.map(node => ({
    ...node,
    id: node.id,
    name: node.name,
    category: node.category_index,
    symbolSize: Math.max(15, Math.min(40, node.name.length * 2 + 10)),
    label: { show: true, fontSize: 10 },
  }));

  const links = rawLinks.map(link => ({
    ...link,
    lineStyle: {
      opacity: 0.7,
      width: 1.5,
      curveness: 0.1,
      type: getLineType(link.label),
      color: getRelationshipColor(link.label, link.document_id, documents)
    }
  }));

  return { nodes, links, categories };
});
// --- End ProcessedGraphData ---

// --- NEW Computed property to filter for connected nodes only ---
const connectedGraphData = computed(() => {
  const { nodes, links, categories } = processedGraphData.value;
  if (links.length === 0) {
    // 如果没有任何连接，则不显示任何节点
    return { nodes: [], links: [], categories };
  }

  const connectedNodeIds = new Set<string>();
  links.forEach(link => {
    connectedNodeIds.add(link.source);
    connectedNodeIds.add(link.target);
  });

  const filteredNodes = nodes.filter(node => connectedNodeIds.has(node.id));

  return {
    nodes: filteredNodes,
    links: links, // 链接保持不变，因为它们定义了连接性
    categories: categories // 类别保持不变，供图例使用
  };
});
// --- End ConnectedGraphData ---


// --- Update filteredGraphData to use connectedGraphData as its base ---
const filteredGraphData = computed(() => {
  // 现在 filteredGraphData 将在 connectedGraphData 的基础上进行搜索过滤
  const { nodes, links, categories } = connectedGraphData.value; // 使用 connectedGraphData

  if (!searchTerm.value.trim()) {
    return { nodes, links, categories }; // 返回所有已连接的数据（如果无搜索词）
  }
  const term = searchTerm.value.toLowerCase();
  
  const directlyMatchedNodes = nodes.filter(node => 
    node.name.toLowerCase().includes(term)
  );
  const directlyMatchedNodeIds = new Set(directlyMatchedNodes.map(n => n.id));

  // 如果直接匹配的节点数为0，但我们希望通过搜索也显示孤立节点（如果它们是搜索结果），
  // 这里的逻辑需要根据需求调整。当前逻辑是：如果搜索词不为空，则只显示与搜索词相关的已连接的节点。
  // 如果你希望即使一个节点没有连接，但只要它匹配搜索词就显示它，那么这里的过滤逻辑需要调整，
  // 并且 drawGraph 可能需要处理 nodes 和 links 不完全匹配的情况（ECharts 可以处理）。
  // 但基于你的原始请求（"没有关系关联的概念也不放进知识图谱中"），当前逻辑优先保证连接性。

  const relatedLinks = links.filter(link => 
    directlyMatchedNodeIds.has(link.source) || directlyMatchedNodeIds.has(link.target)
  );

  const allRelevantNodeIds = new Set<string>(directlyMatchedNodeIds);
  relatedLinks.forEach(link => {
    allRelevantNodeIds.add(link.source);
    allRelevantNodeIds.add(link.target);
  });

  const finalNodes = nodes.filter(node => allRelevantNodeIds.has(node.id));

  return {
    nodes: finalNodes,
    links: relatedLinks, // 只显示与最终节点相关的链接
    categories
  };
});


const filters = ref([
  { label: '显示核心概念', value: true },
  { label: '显示次要概念', value: false },
  // { label: '显示文献间关系', value: true }, // This is implicit with global graph
  { label: '根据相关性着色', value: true } // Might be controlled by category colors now
]);

const layoutControls = ref({
  nodeDistance: 150, // Increased default repulsion for better separation
  linkLength: 100,    // Default link length
  gravityToCategory: 0.2 // Added: Force pulling nodes towards their category center
});

// --- Fetch global graph data ---
async function fetchGlobalGraph() {
  isLoading.value = true;
  try {
    let apiUrl = '/global-graph';
    const loadedDocIds = documentStore.documents.map(doc => doc.id); // Get loaded doc IDs

    if (loadedDocIds.length > 0) {
      const params = new URLSearchParams();
      loadedDocIds.forEach(id => params.append('document_ids', id));
      apiUrl = `/global-graph?${params.toString()}`;
    } else {
      // Optional: Decide what to do if no documents are loaded.
      // Fetch all, or fetch none and show a message.
      // For now, let's assume we fetch all if no IDs, or you can choose to fetch nothing.
      // If you want to fetch nothing:
      // rawGlobalGraphData.value = { nodes: [], links: [], documents: [] };
      // isLoading.value = false;
      // nextTick(() => drawGraph()); // Draw an empty graph
      // return;
    }

    console.log(`[KnowledgeGraphView] Fetching global graph from: ${apiUrl}`);
    const response = await fetch(apiUrl);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data: GlobalGraphData = await response.json();
    rawGlobalGraphData.value = data;
    console.log("[KnowledgeGraphView] Fetched global graph data:", data);
    // After fetching, draw the graph
    nextTick(() => {
        if (!chartInstance && echartsContainerRef.value) initChart();
        else drawGraph();
    });
  } catch (error) {
    console.error("[KnowledgeGraphView] Error fetching global graph data:", error);
    showSnackbar("加载全局图谱失败", "error");
    rawGlobalGraphData.value = null; // Reset on error
  } finally {
    isLoading.value = false;
  }
}
// --- End Fetch ---

const initChart = () => {
  if (echartsContainerRef.value && !chartInstance) { 
    chartInstance = echarts.init(echartsContainerRef.value);
    console.log("[KnowledgeGraphView] ECharts instance initialized.");

    chartInstance.on('click', (params) => {
      if (params.dataType === 'node' && chartInstance) {
        console.log("[KnowledgeGraphView] Node clicked:", params.data.name, "Index:", params.dataIndex);
        chartInstance.dispatchAction({
          type: 'focusNodeAdjacency',
          seriesIndex: 0,
          dataIndex: params.dataIndex
        });
        chartInstance.dispatchAction({
          type: 'highlight',
          seriesIndex: 0,
          dataIndex: params.dataIndex
        });
      } else if (params.dataType === 'edge') {
        console.log("[KnowledgeGraphView] Edge clicked:", params.data);
      }
    });
    drawGraph(); 
  } else if (chartInstance) {
    drawGraph();
  }
};

function showSnackbar(message: string, type: 'error' | 'success' | 'info' = 'info') {
  snackbar.value = {
    visible: true,
    message,
    color: type
  };
}

const drawGraph = () => {
  if (!chartInstance) { // 移除 !filteredGraphData.value 的检查，因为 filteredGraphData 总是会返回一个对象
    return;
  }
  
  const currentData = filteredGraphData.value; // filteredGraphData 现在基于 connectedGraphData
  
  // 即使 currentData.nodes 为空 (例如，所有节点都被过滤掉了，或者初始就没有连接的节点)，
  // 我们也应该清除图表或显示空状态，而不是直接返回。
  // isLoading 的处理保持不变，由 fetchGlobalGraph 控制。

  if (currentData.nodes.length === 0 && currentData.links.length === 0) { // 同时检查链接
    chartInstance.clear(); 
    // 你可能想在这里再次检查 isLoading，如果不是 loading 状态，则显示"无数据"的提示
    // 这个空状态提示已经在模板中处理了:
    // <div v-else-if="!processedGraphData || processedGraphData.nodes.length === 0" ...>
    // 我们可以让 ECharts clear()。
    // 但要注意，如果 processedGraphData 有数据，只是 filteredGraphData 变空，
    // 那么模板中的那个 v-else-if 可能不会触发。
    // 或许需要调整模板中的条件，或者在 drawGraph 中直接处理空状态的视觉反馈。
    // 为了简单起见，先让 ECharts clear()。
    return;
  }

  const option: EChartsOption = {
    tooltip: {
      formatter: (params: any) => {
        if (params.dataType === 'node') return `概念: ${params.data.name}`;
        if (params.dataType === 'edge') {
          const edgeLabel = params.data.label ? `[${params.data.label}]` : '';
          return `${params.data.source} ${edgeLabel} → ${params.data.target}`;
        }
        return '';
      }
    },
    legend: currentData.categories.length > 1 ? [{
        data: currentData.categories.map(function (a) {
            return a.name;
        }),
        orient: 'vertical',
        left: 'left',
        top: 'middle',
        itemGap: 5,
        textStyle: { fontSize: 10 }
    }] : [],
    series: [
      {
        type: 'graph',
        layout: 'force',
        nodes: currentData.nodes, // 使用过滤后的节点
        links: currentData.links,   // 使用过滤后的链接 (或者全部链接，如果 finalNodes 保证了链接的有效性)
        categories: currentData.categories,
        roam: true,
        draggable: true,
        label: {
          show: true,
          position: 'right',
          formatter: '{b}',
          fontSize: 10,
        },
        edgeLabel: { 
            show: true,
            formatter: (params: any) => {
              const label = params.data.label || '';
              return label;
            },
            fontSize: 9, 
            padding: [2, 4],
            backgroundColor: 'rgba(255, 255, 255, 0.7)',
            borderRadius: 2,
            color: '#333',
            align: 'center',
            verticalAlign: 'middle',
            overflow: 'truncate',
            width: 60, 
        },
        lineStyle: {
          opacity: 0.7,
          width: 1.5,
          curveness: 0.1
        },
        emphasis: {
          focus: 'adjacency',
          label: { show: true, fontWeight: 'bold', fontSize: 12 }, 
          edgeLabel: {
            show: true,
            fontSize: 9, 
            fontWeight: 'bold',
            formatter: (params: any) => params.data.label || '',
            overflow: 'truncate',
            width: 70, 
          },
          lineStyle: { width: 2.5, opacity: 1 }
        },
        force: {
          repulsion: layoutControls.value.nodeDistance,
          edgeLength: layoutControls.value.linkLength,
          gravity: layoutControls.value.gravityToCategory,
          friction: 0.6,
        },
        labelLayout: {
            hideOverlap: true 
        },
        select: {
            itemStyle: {
                borderColor: '#fac858',
                borderWidth: 2
            },
            label: {
                show: true,
                fontWeight: 'bold',
                fontSize: 14
            }
        }
      } as GraphSeriesOption
    ]
  };
  chartInstance.setOption(option, { notMerge: false, lazyUpdate: false });

  const termFromStore = conceptToHighlightInGraph.value; 
  if (termFromStore && chartInstance) {
    console.log(`[KnowledgeGraphView] Attempting to highlight based on store: ${termFromStore}`);
    const nodeToHighlight = currentData.nodes.find(n => n.name === termFromStore);
    
    if (nodeToHighlight) {
      const nodeIndex = currentData.nodes.indexOf(nodeToHighlight);
      console.log(`[KnowledgeGraphView] Found node '${termFromStore}' at index ${nodeIndex} in filtered data. Dispatching actions.`);
      chartInstance.dispatchAction({
        type: 'focusNodeAdjacency',
        seriesIndex: 0,
        dataIndex: nodeIndex,
      });
      chartInstance.dispatchAction({
        type: 'highlight',
        seriesIndex: 0,
        dataIndex: nodeIndex,
      });
    } else {
      console.warn(`[KnowledgeGraphView] Node '${termFromStore}' not found in current filteredGraphData.`);
      showSnackbar(`概念 "${termFromStore}" 未在当前图谱中找到。`, 'info');
    }
    
    if (documentStore.clearConceptToHighlight) {
        documentStore.clearConceptToHighlight();
        console.log(`[KnowledgeGraphView] Cleared concept from store: ${termFromStore}`);
    } else {
        console.warn("[KnowledgeGraphView] documentStore.clearConceptToHighlight is not defined!");
    }
  }
};

const throttledDrawGraph = throttle(() => {
  if (chartInstance) {
    drawGraph();
  }
}, 300, { leading: false, trailing: true });


const resizeObserver = ref<ResizeObserver | null>(null);

const setupResizeObserver = () => {
    if (graphWrapperRef.value) {
        resizeObserver.value = new ResizeObserver(entries => {
            throttledResizeChart();
        });
        resizeObserver.value.observe(graphWrapperRef.value);
    }
};

const cleanupResizeObserver = () => {
    if (resizeObserver.value && graphWrapperRef.value) {
        resizeObserver.value.unobserve(graphWrapperRef.value);
    }
    resizeObserver.value = null;
};


const throttledResizeChart = throttle(() => {
    requestAnimationFrame(() => {
        if (chartInstance && echartsContainerRef.value) {
            const container = echartsContainerRef.value;
            const newWidth = container.clientWidth;
            const newHeight = container.clientHeight;
            
            if (newWidth > 0 && newHeight > 0) { 
                chartInstance.resize({
                    width: newWidth,
                    height: newHeight
                });
            } else {
            }
        }
    });
}, 200);


const toggleFullScreen = async () => {
  if (!graphWrapperRef.value) return;
  try {
    if (!document.fullscreenElement) {
      await graphWrapperRef.value.requestFullscreen();
    } else {
      if (document.exitFullscreen) {
        await document.exitFullscreen();
      }
    }
  } catch (err) {
    console.error("Fullscreen API error:", err);
  }
};

const handleFullScreenChange = () => {
    isFullScreen.value = !!document.fullscreenElement;
    nextTick(() => { 
        chartInstance?.resize();
    });
};


onMounted(() => {
  fetchGlobalGraph(); // Fetch data on mount
  // initChart will be called by fetchGlobalGraph after data is received
  setupResizeObserver();
  document.addEventListener('fullscreenchange', handleFullScreenChange);
});

onBeforeUnmount(() => {
  chartInstance?.dispose();
  cleanupResizeObserver();
  document.removeEventListener('fullscreenchange', handleFullScreenChange);
});

// Watch for changes in filtered data (e.g. due to searchTerm) to redraw
watch(filteredGraphData, () => {
  if (chartInstance) {
    throttledDrawGraph();
  } else if (echartsContainerRef.value && rawGlobalGraphData.value) { 
    // If chart was not initialized but data is present (e.g. HMR)
    nextTick(() => initChart());
  }
}, { deep: true, immediate: false }); 

// No longer watch currentDocument for graph data, using global fetch instead
// watch(currentDocument, (newDoc, oldDoc) => { ... });

watch(isFullScreen, () => { 
    nextTick(() => {
        chartInstance?.resize();
    });
});

watch(controlsDrawer, (isOpen) => {
  setTimeout(() => {
    if (chartInstance) {
      throttledResizeChart();
    }
  }, 350); 
});

// Helper function (already exists, ensure it's used or adapted)
const getLineType = (label: string | undefined): string => {
  if (!label) return 'solid';
  if (label.includes('并列')) return 'dashed';
  if (label.includes('修饰')) return 'dotted';
  if (label.includes('主语') || label.includes('宾语')) return 'solid';
  return 'solid';
};

// Modified to take documentId and documents for category color consistency
const getRelationshipColor = (label: string | undefined, linkDocumentId: string, documents: GlobalGraphDocument[]): string => {
  // Try to match link color to its source document's category color
  const docIndex = documents.findIndex(d => d.id === linkDocumentId);
  if (docIndex !== -1 && chartInstance) { // Check if chartInstance exists to get colors
    const option = chartInstance.getOption();
    if (option && option.color && docIndex < (option.color as string[]).length) {
      // @ts-ignore
      return option.color[docIndex % (option.color as string[]).length]; // Use ECharts theme color for the category
    }
  }
  // Fallback colors if category color not found or for generic labels
  if (!label) return '#aaa';
  if (label.includes('并列')) return '#1890ff'; 
  if (label.includes('修饰')) return '#52c41a'; 
  if (label.includes('主语') || label.includes('宾语')) return '#fa8c16'; 
  if (label.includes('关联')) return '#722ed1'; 
  return '#aaa'; 
};

</script>

<style scoped>
.knowledge-graph-view {
  /* fill-height and d-flex flex-column are applied directly */
}

.graph-main-content {
  /* flex-grow-1 is applied directly */
  position: relative; /* Needed for absolute positioning of children if any, or for observer */
  background-color: #F0FFFF; /* For debugging */
  width: 1120px;
}

.echarts-graph-container {
  width: 100%;
  height: 100%; 
}

.graph-main-content:fullscreen {
  padding: 0 !important;
  margin: 0 !important;
  background-color: white; 
}
.graph-main-content:fullscreen .echarts-graph-container {
    border: none !important;
}

.control-panel-drawer {
}

.v-list-subheader {
    font-weight: 500;
    color: rgba(0,0,0,0.6);
}
</style> 