import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface Relationship {
  source: string;
  target: string;
  label?: string;
}

// Define the new SegmentDifficultyMarker interface
export interface SegmentDifficultyMarker {
  segment_id: string; // e.g., "p0_b3"
  page_index: number;
  block_index_on_page: number;
  text_preview: string;
  score: number;
  reasons: string[];
}

// Remove or comment out the old PageDifficultyMarker if it exists
/*
export interface PageDifficultyMarker {
  page_index: number; // 0-based
  score: number;
  reasons: string[];
}
*/

export interface Document {
  id: string
  title: string
  authors: string[]
  year: string | null
  abstract: string
  content: string[]
  filePath?: string
  fileName: string
  fileType: string
  fileSize: number
  uploadDate: Date
  lastReadDate: Date
  tags: string[]
  concepts: Array<{ term: string, definition: string | null }>
  favorite?: boolean
  readStatus?: 'read' | 'unread' | 'reading'
  selected?: boolean
  blobUrl?: string
  relationships: Relationship[]
  difficulty_markers?: SegmentDifficultyMarker[] // MODIFIED HERE: Use new interface
}

interface UploadedDocData {
  id: string;
  title: string;
  concepts: Array<{ term: string, definition: string | null }>;
  relationships: Relationship[];
  difficulty_markers?: SegmentDifficultyMarker[]; // MODIFIED HERE: Use new interface
}

export const useDocumentStore = defineStore('documents', () => {
  const documents = ref<Document[]>([])
  const currentDocumentId = ref<string | null>(null)
  const conceptToHighlightInGraph = ref<string | null>(null);
  const blobUrlMap = ref<Record<string, string>>({});

  const currentDocument = computed(() => 
    documents.value.find(doc => doc.id === currentDocumentId.value) || null
  )

  // Action to add a complete Document object (e.g., for samples or future use)
  function addDocument(document: Document) {
    if (documents.value.some(doc => doc.id === document.id)) {
        console.warn(`[DocumentStore] Document with ID ${document.id} already exists. Skipping add.`);
        return;
    }
    documents.value.unshift(document);
    console.log("[DocumentStore] Document added via addDocument. Current count:", documents.value.length);
  }

  // Action to add a document processed by the backend
  function addUploadedDocument(data: UploadedDocData, originalFile?: File) {
    console.log("[DocumentStore] Adding uploaded document:", data, "Original file:", originalFile);
    if (documents.value.some(doc => doc.id === data.id)) {
        console.warn(`[DocumentStore] Document with ID ${data.id} already exists. Skipping add.`);
        return;
    }

    let generatedBlobUrl: string | undefined = undefined;
    if (originalFile) {
      try {
        generatedBlobUrl = URL.createObjectURL(originalFile);
        blobUrlMap.value[data.id] = generatedBlobUrl; // Store for potential revocation
        console.log(`[DocumentStore] Created Blob URL for ${originalFile.name}: ${generatedBlobUrl}`);
      } catch (error) {
        console.error("[DocumentStore] Failed to create Blob URL:", error);
      }
    }

    const newDocument: Document = {
      id: data.id,
      title: data.title || (originalFile?.name || 'Untitled Document'),
      authors: [],
      year: null,
      abstract: '',
      content: [],
      fileName: originalFile?.name || 'unknown.pdf',
      fileType: originalFile?.type || 'application/pdf',
      fileSize: originalFile?.size || 0,
      uploadDate: new Date(),
      lastReadDate: new Date(),
      tags: [],
      concepts: data.concepts || [],
      favorite: false,
      readStatus: 'unread',
      blobUrl: generatedBlobUrl,
      relationships: data.relationships || [],
      difficulty_markers: data.difficulty_markers || [],
    };
    
    console.log("[DocumentStore] Created new document object:", newDocument);
    documents.value.unshift(newDocument);
    console.log("[DocumentStore] Document added. Current count:", documents.value.length);
  }

  // 删除文献 - Also revoke blob URL if exists
  function removeDocument(documentId: string) {
    const index = documents.value.findIndex(doc => doc.id === documentId)
    if (index !== -1) {
      // Revoke blob URL before removing document data
      if (blobUrlMap.value[documentId]) {
        URL.revokeObjectURL(blobUrlMap.value[documentId]);
        delete blobUrlMap.value[documentId];
        console.log(`[DocumentStore] Revoked Blob URL for document ID: ${documentId}`);
      }
      documents.value.splice(index, 1)
      if (currentDocumentId.value === documentId) {
        currentDocumentId.value = documents.value.length > 0 ? documents.value[0].id : null
      }
    }
  }

  // 设置当前阅读的文献
  function setCurrentDocument(documentId: string) {
    const doc = documents.value.find(doc => doc.id === documentId)
    if (doc) {
      currentDocumentId.value = documentId
      if (doc.lastReadDate.toDateString() !== new Date().toDateString()) {
          doc.lastReadDate = new Date()
      }
    } else {
        console.warn(`[setCurrentDocument] Document with ID ${documentId} not found.`)
        currentDocumentId.value = null;
    }
  }

  // 更新文献
  function updateDocument(documentId: string, updates: Partial<Document>) {
    const index = documents.value.findIndex(doc => doc.id === documentId)
    if (index !== -1) {
      documents.value[index] = { ...documents.value[index], ...updates }
    }
  }

  // 添加模拟数据（开发测试用）
  function addSampleDocuments() {
    if (documents.value.length === 0) {
      const sampleDocs: Document[] = [
        {
          id: '1',
          title: '知识图谱在学术文献理解中的应用',
          authors: ['张三', '李四'],
          year: '2023',
          abstract: '本研究探讨了知识图谱技术在学术文献理解和知识提取中的应用。通过构建实体关系网络，可以更有效地梳理复杂文献中的核心概念和关系，为研究人员提供更直观的知识导航。',
          content: Array(20).fill(0).map((_, i) => 
            i === 0 ? '知识图谱(Knowledge Graph)是一种用图结构表示知识的技术，通过节点和边分别表示实体和关系。在学术文献理解中，知识图谱可以帮助识别文章中的核心概念、术语以及它们之间的关联。' :
            i === 1 ? '近年来，随着人工智能和自然语言处理技术的发展，知识图谱在学术领域的应用越来越广泛。研究人员利用知识图谱处理大量学术文献，自动抽取关键信息并建立联系，从而更好地把握研究动态和知识脉络。' :
            `这是第${i+1}段示例内容，详细说明知识图谱在学术文献理解中的应用和优势。通过这种方式组织知识，研究人员可以更快地定位相关研究，发现知识间的隐含联系。`
          ),
          fileName: '知识图谱应用研究.pdf',
          fileType: 'application/pdf',
          fileSize: 1240000,
          uploadDate: new Date('2023-10-15'),
          lastReadDate: new Date('2023-10-20'),
          tags: ['知识图谱', '自然语言处理', '学术文献'],
          concepts: [
            { term: '知识图谱', definition: '一种结构化的知识表示方法，通过图的形式组织信息，节点表示实体，边表示关系。' },
            { term: '实体识别', definition: '从非结构化文本中识别出命名实体（如人名、地名、组织名等）的过程。' },
            { term: '关系抽取', definition: '识别文本中实体之间关系的过程，是构建知识图谱的关键步骤。' },
            { term: '学术文献', definition: '指在特定学科领域内，经过同行评审并发表的研究论文、报告或书籍。' },
            { term: '自然语言处理', definition: '人工智能领域的一个分支，研究如何让计算机理解、解释和生成人类语言。' },
            { term: '网络', definition: '指为实现特定目的而应用科学知识的系统化方法、技能和设备。' },
            { term: '网络2', definition: '指为实现特定目的而应用科学知识的系统化方法、技能和设备。' },
            { term: '网络3', definition: '指为实现特定目的而应用科学知识的系统化方法、技能和设备。' },
            { term: '网络4', definition: '指为实现特定目的而应用科学知识的系统化方法、技能和设备。' }
          ],
          relationships: [],
          difficulty_markers: [],
        },
        {
          id: '2',
          title: '心流理论与学习效率研究',
          authors: ['王五', '赵六'],
          year: '2022',
          abstract: '本研究基于心理学中的心流理论（Flow Theory），探讨了在学习过程中如何通过适当的挑战性与技能平衡，帮助学习者达到心流状态，从而显著提高学习效率和体验质量。',
          content: Array(15).fill(0).map((_, i) => 
            i === 0 ? '心流理论是由心理学家米哈里·契克森米哈伊（Mihaly Csikszentmihalyi）提出的一种心理状态，指人在全神贯注于某项活动时所体验到的一种完全投入的感觉。在这种状态下，人会忘记时间的流逝，获得高度的满足感。' :
            i === 1 ? '在学习过程中，当学习者面临的挑战与其技能水平相匹配时，最容易进入心流状态。太简单的任务会导致无聊，太困难的任务则会引起焦虑。适当的挑战-技能平衡是达到心流的关键。' :
            `这是第${i+1}段示例内容，详细探讨心流理论在学习中的应用。研究表明，心流状态可以提高注意力集中度，增强记忆力，并使学习过程更加愉悦。`
          ),
          fileName: '心流理论与学习.pdf',
          fileType: 'application/pdf',
          fileSize: 980000,
          uploadDate: new Date('2022-08-10'),
          lastReadDate: new Date('2022-09-05'),
          tags: ['心流理论', '学习效率', '认知心理学'],
          concepts: [
            { term: '心流状态', definition: '人在全神贯注于某项活动时达到的最佳心理体验状态，特点是高度专注、时间感扭曲和内在愉悦。' },
            { term: '挑战-技能平衡', definition: '心流理论中的核心概念，指任务难度与个人能力水平相匹配的状态。' },
            { term: '内在动机', definition: '由个体内部产生的参与活动的动力，如兴趣、好奇心或享受感，而非外部奖励。' },
            { term: '心理学', definition: '研究人类及动物心理现象、精神功能和行为的科学。' },
            { term: '学习效率', definition: '指学习者在单位时间内获取知识或技能的程度。' }
          ],
          relationships: [],
          difficulty_markers: [],
        }
      ]
      
      // Use the specific addDocument action here
      sampleDocs.forEach(doc => addDocument(doc)) 
      if (sampleDocs.length > 0) {
        currentDocumentId.value = sampleDocs[0].id
      }
    }
  }

  // Action to set the concept to highlight
  function setConceptToHighlight(term: string | null) {
    conceptToHighlightInGraph.value = term;
    if (term) {
      console.log(`[DocumentStore] Set concept to highlight: ${term}`);
    } else {
      console.log(`[DocumentStore] Cleared concept to highlight via setConceptToHighlight(null).`);
    }
  }

  // Action to clear the concept to highlight
  function clearConceptToHighlight() {
    conceptToHighlightInGraph.value = null;
    console.log(`[DocumentStore] Concept to highlight explicitly cleared.`);
  }

  return { 
    documents, 
    currentDocumentId, 
    currentDocument, 
    addDocument,
    addUploadedDocument,
    removeDocument, 
    setCurrentDocument, 
    updateDocument,
    addSampleDocuments,
    conceptToHighlightInGraph,
    setConceptToHighlight,
    clearConceptToHighlight,
    blobUrlMap
  }
}) 