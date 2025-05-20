# flake8: noqa
# -*- coding: utf-8 -*-
"""Backend API using FastAPI for MindFlow Reader."""

import io
import logging
import uuid
from pathlib import Path
import re # Import regex for filtering
import urllib.parse # Add urllib.parse import
import requests # Add this import

import fitz  # PyMuPDF
from hanlp_restful import HanLPClient # Import HanLPClient
# import torch # Remove PyTorch import
from fastapi import FastAPI, File, HTTPException, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional


# --- Global Configuration & Setup ---

# --- HanLP API Configuration ---
# !!! 密钥已设置，建议后续使用环境变量或配置文件管理 !!!
# HANLP_API_URL = "https://hanlp.hankcs.com/api/v1/parse" # Remove old V1 constant
HANLP_BASE_URL = "https://www.hanlp.com/api" # Confirmed correct base URL for the client
HANLP_API_KEY = "ODM5M0BiYnMuaGFubHAuY29tOlNMTHZkcjhHM01NenRQN1Q=" # 密钥已填入

# --- Wikipedia Concept Validation Configuration ---
# ENABLE_WIKIPEDIA_CONCEPT_VALIDATION = True # Toggle for Wikipedia validation step # Removed
# --- End Wikipedia Concept Validation Configuration ---

# --- Local Wikipedia Titles Corpus ---
WIKIPEDIA_TITLES_FILE = "zhwiki-latest-all-titles-in-ns0-simplified" # Assumed to be in the same directory as main.py
LOCAL_WIKIPEDIA_TITLES_SET = set()
# --- End Local Wikipedia Titles Corpus ---


# --- Initialize HanLPClient ---
HanLP_Client = None
# 1. Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Load Local Wikipedia Titles ---
def load_local_wikipedia_titles():
    """Loads Wikipedia titles from the local file into a set."""
    global LOCAL_WIKIPEDIA_TITLES_SET
    try:
        file_path = Path(__file__).parent / WIKIPEDIA_TITLES_FILE
        if not file_path.exists():
            logger.error(f"Local Wikipedia titles file not found: {file_path}. Concept filtering by local corpus will be disabled.")
            LOCAL_WIKIPEDIA_TITLES_SET = set() # Ensure it's an empty set
            return

        with open(file_path, "r", encoding="utf-8") as f:
            titles = {line.strip() for line in f if line.strip()}
        LOCAL_WIKIPEDIA_TITLES_SET = titles
        logger.info(f"Successfully loaded {len(LOCAL_WIKIPEDIA_TITLES_SET)} titles from '{WIKIPEDIA_TITLES_FILE}' into local corpus set.")
    except Exception as e:
        logger.error(f"Error loading local Wikipedia titles from '{WIKIPEDIA_TITLES_FILE}': {e}", exc_info=True)
        LOCAL_WIKIPEDIA_TITLES_SET = set() # Ensure it's an empty set on error

load_local_wikipedia_titles() # Load at startup
# --- End Load Local Wikipedia Titles ---

try:
    if HANLP_API_KEY and HANLP_API_KEY != "YOUR_HANLP_API_KEY": # Check if key is set
        HanLP_Client = HanLPClient(HANLP_BASE_URL, auth=HANLP_API_KEY, language='zh')
        # Optional: Perform a simple test call to check connectivity/auth
        HanLP_Client.parse('初始化测试')
        logger.info(f"HanLPClient initialized successfully for URL: {HANLP_BASE_URL} with authentication.")
    else:
        logger.error("HanLP API Key is not set. HanLPClient will not be initialized. Concept extraction unavailable.")
except Exception as e:
    logger.error(f"Failed to initialize HanLPClient or test connection: {e}", exc_info=True)
    HanLP_Client = None # Ensure it's None if initialization fails
# --- End HanLPClient Initialization ---

# --- Mock Global Knowledge Store ---
# In a real application, this would be a connection to a graph database (Neo4j) or a structured relational database.
# For demonstration, we use simple Python dictionaries and sets.
global_knowledge_graph = {
    "nodes": {},  # { "concept_term": { "name": "concept_term", "document_ids": set(), ...other_attrs } }
    "edges": set(), # { ("source_term", "target_term", "label", "document_id") }
    "documents": {} # { "document_id": { "title": "doc_title", ... } }
}
# --- End Mock Global Knowledge Store ---

class TextProcessingRequest(BaseModel):
    """Request model for processing raw text."""
    text: str
    language: str | None = None  # Optional: Hint for language processing

class Concept(BaseModel):
    """Represents a single extracted concept."""
    term: str
    # definition: str | None = None # Definition fetching moved to separate endpoint

class ConceptListResponse(BaseModel):
   """Response model for a list of concepts (used by /extract-concepts)."""
   concepts: list[Concept]

class Relationship(BaseModel):
    """Represents a relationship between two concepts."""
    source: str
    target: str
    label: str | None = None # Added label for relationship type
    # Later, we can add: type: str = "co-occurrence"

class PageDifficultyMarker(BaseModel):
    """Represents the calculated difficulty for a single page."""
    page_index: int # 0-based index of the page
    score: float      # Calculated difficulty score (e.g., 0-1 or simple count)
    reasons: list[str] # List of reasons contributing to the score (e.g., ["high_term_density", "formulas_present"])

class SegmentDifficultyMarker(BaseModel):
    """Represents the calculated difficulty for a single text segment (e.g., a paragraph/block)."""
    segment_id: str                 # Unique ID, e.g., "p0_b3" (page 0, block 3)
    page_index: int                 # 0-based page index this segment belongs to
    block_index_on_page: int        # 0-based block index on that page (from fitz)
    text_preview: str               # First ~100 chars of the block text for context
    score: float
    reasons: list[str]
    # Optional: rect: tuple[float, float, float, float] | None = None # For future use

class DocumentUploadResponse(BaseModel):
    """Response model after successful PDF upload and processing."""
    id: str
    title: str
    concepts: list[dict] # Expecting list of {term: str, definition: str | None}
    relationships: list[Relationship] # Added for graph structure
    difficulty_markers: list[SegmentDifficultyMarker] # MODIFIED HERE
    # page_count: int # Optional: could add page count too

class GlobalGraphResponseNode(BaseModel):
    id: str # Concept term
    name: str # Concept term
    document_ids: list[str]
    # Add other potential node attributes for ECharts if needed, e.g., symbolSize, category
    category_index: int | None = None # Index for ECharts category based on primary document

class GlobalGraphResponseLink(BaseModel):
    source: str # Source concept term
    target: str # Target concept term
    label: str | None
    document_id: str # The document this link was primarily extracted from

class GlobalGraphResponseDocument(BaseModel):
    id: str
    title: str

class GlobalGraphResponse(BaseModel):
    """Response model for the global knowledge graph."""
    nodes: list[GlobalGraphResponseNode]
    links: list[GlobalGraphResponseLink]
    documents: list[GlobalGraphResponseDocument] # To map document_ids to titles for category names

class DefinitionResponse(BaseModel):
    """Response model for a term definition."""
    term: str
    definition: str | None

# --- Helper Functions ---

# Default POS patterns configuration (PKU tagset)
DEFAULT_POS_CONFIG = {
    'noun_tags': ('n', 'nr', 'ns', 'nt', 'nz'),
    'adj_tags': ('a',),
    'verb_tags': ('v',),
}

# Relation label mapping for better readability
RELATION_LABEL_MAPPING = {
    # 通用依存关系
    "dep": "关联",
    "root": "核心",
    # 并列关系
    "conj": "并列",
    # 修饰关系
    "amod": "形容词修饰",
    "advmod": "副词修饰",
    # 名词相关
    "compound:nn": "名词修饰",
    "nsubj": "主语",
    "nsubjpass": "被动主语",
    "dobj": "宾语",
    "iobj": "间接宾语",
    # 句法关系
    "aux": "助词",
    "cop": "系动词",
    "mark": "标记",
    "cc": "并列连词",
    "clf": "分类词",
    "discourse": "话语",
    # 修饰
    "acl": "名词子句",
    "advcl": "副词子句",
    "det": "限定词",
    "nummod": "数量修饰",
    # 其他补充
    "case": "格标记",
    "lobj": "方位宾语",
    "loc": "位置",
    "pccomp": "补语补足",
    "pobj": "介词宾语",
    "prep": "介词",
    "xcomp": "开放补语",
    "ccomp": "从句补语",
    "rcmod": "相对从句"
}

# Minimal set of stopwords for basic concept filtering when using DEP for relationships
DEFAULT_STOPWORDS = {
    # Chinese Common Particles/Words
    "的", "了", "是", "和", "在", "中", "上", "下", "我", "你", "他", "她", "它", "们",
    "这", "那", "一个", "一些", "这个", "那个", "也", "与", "或", "但", "就", "都",
    # English Common Words
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "with",
    "and", "or", "but", "is", "are", "was", "were", "be", "been", "being",
    "it", "its", "this", "that", "these", "those", "i", "you", "he", "she", "we", "they",
    # Specific low-value words from previous examples if they become concepts
    # "在一起", "有效的", "离不开" # These are better handled by RELATION_STOPWORDS if they are part of relations
}

RELATION_STOPWORDS = {
    # Common function words and low-content words often found in co-occurrence
    "的", "了", "是", "和", "在", "有", "以", "其", "一个", "这个", "那个", "这些", "那些", "一些",
    "一种", "这种", "什么", "如何", "为什么", "何时", "何地", "某", "其他", "其他相关",
    "与", "或", "但", "也", "等", "之", "为", "就", "从", "到", "使", "让", "对", "于", "及", "则", "而", "并",
    "所", "把", "被", "给", "像", "即", "若", "故", "因", "只",
    "不是", "可以", "不可", "能够", "必须", "需要", "应该", "可能", "会", "将",
    "进行", "通过", "作为", "成为", "存在", "发生", "出现", "包含", "包括", "涉及",
    "显示", "表明", "指出", "认为", "建议", "描述", "说明", "解释", "证实", "支持",
    "发展", "影响", "推动", "导致", "产生", "实现", "解决", "应用", "使用", "利用",
    "研究", "分析", "讨论", "介绍", "提出", "比较", "总结",
    "方面", "问题", "方法", "结果", "作用", "过程", "情况", "内容", "部分", "形式", "类型", "结构",
    "模式", "程度", "数量", "关系", "特点", "特征", "优势", "劣势", "原因", "目的", "意义",
    "主要", "重要", "基本", "常见", "不同", "相同", "类似", "相关", "一般", "具体", "特定",
    "首先", "其次", "然后", "最后", "此外", "另外", "同时", "通常", "目前", "现在", "未来",
    "更", "最", "很", "太", "都", "也", "还", "仅", "不再", "几乎", "大约", "左右",
    # Words from user's example that are bad for relationships
    # "在一起", "有效的", "离不开", # These are better handled if they are concepts, by filtering concepts themselves
    # Single characters (often noise in Chinese if not part of a known concept)
    # English prepositions and articles if they somehow become concepts
    "a", "an", "the", "in", "on", "at", "of", "to", "for", "with", "by", "from", "up", "down", "out", "over", "under",
    # English auxiliary verbs
    "is", "are", "was", "were", "be", "been", "being", "has", "had", "have", "do", "does", "did",
    "can", "could", "will", "would", "may", "might", "must", "should",
}

def _extract_relations_from_dep(doc: dict, 
                                final_concepts_set: set[str], 
                                tok_task_name: str = 'tok/coarse', 
                                dep_task_name: str = 'dep') -> set[tuple[str, str, str | None]]:
    """Extracts undirected relationships (concept1, concept2, label) based on dependency parsing.
       This is a highly simplified initial version.
    """
    extracted_word_level_triples = set() # Stores (dep_word_text, rel_label, head_word_text)
    
    sentences_tokens = doc.get(tok_task_name, [])
    sentences_dep_info = doc.get(dep_task_name, [])

    if not (sentences_tokens and sentences_dep_info and len(sentences_tokens) == len(sentences_dep_info)):
        logger.warning("Tokenized sentences or dependency info is missing or mismatched. Skipping DEP relation extraction.")
        return set() # Return empty set of (c1,c2) pairs

    for sent_idx, tokens_in_sentence in enumerate(sentences_tokens):
        if not tokens_in_sentence or sent_idx >= len(sentences_dep_info):
            continue
        
        dep_info_for_sentence = sentences_dep_info[sent_idx]
        
        if len(tokens_in_sentence) != len(dep_info_for_sentence):
            logger.warning(f"Mismatch in token count and dependency info count for sentence {sent_idx}. Skipping this sentence.")
            continue

        # Identify concepts present in the current sentence and their 0-based indices
        # This simplified version assumes concepts are single tokens and matches lowercase.
        sentence_concepts_map = {} # {token_idx_0_based: concept_text (lowercased)}
        for i, token_text in enumerate(tokens_in_sentence):
            tt_lower = token_text.lower()
            if tt_lower in final_concepts_set:
                sentence_concepts_map[i] = tt_lower

        for word_idx_0_based, dep_arc in enumerate(dep_info_for_sentence):
            head_idx_1_based = dep_arc[0]
            relation_label = dep_arc[1]

            if head_idx_1_based == 0: # Current word is ROOT or unattached
                continue
                
            head_idx_0_based = head_idx_1_based - 1 # Convert to 0-based index
            
            # Check if both the dependent and the head are part of our identified concepts for this sentence
            dependent_concept = sentence_concepts_map.get(word_idx_0_based)
            head_concept = sentence_concepts_map.get(head_idx_0_based)

            if dependent_concept and head_concept:
                # Filter out self-loops
                if dependent_concept == head_concept:
                    continue
                
                # Filter if either concept is a stopword for relationships
                if dependent_concept in RELATION_STOPWORDS or head_concept in RELATION_STOPWORDS:
                    logger.debug(f"[DEP Relation Filter] Skipped ({dependent_concept}, {relation_label}, {head_concept}) due to stopword.")
                    continue

                # Filter out purely punctuation relationships or other undesirable low-level technical labels if needed
                # Example: if relation_label.lower() in ['punct', 'dep', 'case', 'mark']:
                # continue
                
                # Map relation label to more human-readable form
                readable_label = RELATION_LABEL_MAPPING.get(relation_label, relation_label)
                
                # Store the raw word-level triple for now (dependent_concept, readable_relation_label, head_concept)
                # For a simple undirected graph of concepts, we will sort and store later.
                extracted_word_level_triples.add((dependent_concept, readable_label, head_concept))

    # Post-process the extracted word-level triples to form concept-to-concept relationships
    final_relationships = set() # Stores (concept1, concept2, label) tuples
    for dep_c, rel, head_c in extracted_word_level_triples:
        # We want to keep the original direction of dependency relations to preserve semantics
        # but for ease of visualization, we might standardize source/target order
        # Remove sorting logic to maintain direction, but keep semantic relation type
        # We will not go through if dep_c < head_c: logic - we want to keep all relations
        final_relationships.add((dep_c, head_c, rel))

    logger.info(f"Extracted {len(final_relationships)} unique relationships using DEP (simplified, with labels). Details: {len(extracted_word_level_triples)} raw word-level triples.")
    return final_relationships

def _extract_noun_phrases_from_pos(tokens: list[str], tags: list[str], pos_config: dict = DEFAULT_POS_CONFIG) -> set[str]:
    """Extracts potential noun phrases based on POS patterns."""
    phrases = set()
    n = len(tokens)
    if n == 0 or n != len(tags):
        return phrases

    noun_tags = pos_config.get('noun_tags', ())
    adj_tags = pos_config.get('adj_tags', ())
    verb_tags = pos_config.get('verb_tags', ())

    i = 0
    while i < n:
        tag = tags[i]
        token = tokens[i]

        # Helper to add phrases after stripping and lowercasing, ensuring not empty
        def add_cleaned_phrase(p_set, phrase_str):
            cleaned = phrase_str.strip().lower()
            if cleaned: # Only add if not empty after cleaning
                p_set.add(cleaned)

        # --- Improved Patterns --- 
        # current_phrase = "" # No longer used like this
        # Pattern 1: Single Noun
        if tag.startswith(noun_tags):
            # current_phrase = token # Original single noun
            add_cleaned_phrase(phrases, token) # Add normalized single noun
            # Pattern 2: Noun + Noun sequence (NN or NNN)
            if i + 1 < n and tags[i+1].startswith(noun_tags):
                phrase_nn_str = token + tokens[i+1]
                add_cleaned_phrase(phrases, phrase_nn_str)
                if i + 2 < n and tags[i+2].startswith(noun_tags):
                    # phrases.add((phrase_nn + tokens[i+2]).lower()) # Original
                    add_cleaned_phrase(phrases, phrase_nn_str + tokens[i+2])
            # No increment for i here, handled by outer loop or specific patterns
        # Pattern 3: Adjective + Noun (A+N)
        elif tag in adj_tags and i + 1 < n and tags[i+1].startswith(noun_tags):
            # current_phrase = token + tokens[i+1] # Original A+N
            add_cleaned_phrase(phrases, token + tokens[i+1])
            # i += 2 # Original increment, if we only take A+N and move on.
                      # If we want A to also combine with N+N, then i should only increment by 1 here.
        # Pattern 4: Verb + Noun (V+N)
        elif tag in verb_tags and i + 1 < n and tags[i+1].startswith(noun_tags):
            # current_phrase = token + tokens[i+1] # Original V+N
            add_cleaned_phrase(phrases, token + tokens[i+1])
            # i += 2 # Similar to A+N
        
        # General sliding window for N-grams (e.g., up to 5-grams)
        # This will generate many candidates, to be filtered by the Wikipedia titles set.
        # This is added *in addition* to the more specific POS patterns above, or could replace them.
        # Let's make it additive for now to capture both specific linguistic patterns and general N-grams.
        MAX_NGRAM_LEN = 6 # Max length of N-gram to consider (e.g., up to 6 words)
        for k in range(MAX_NGRAM_LEN):
            if i + k < n:
                # Form an N-gram of length k+1 starting at index i
                ngram_tokens = tokens[i : i + k + 1]
                # Optional: Add heuristics here, e.g., must start/end with noun, or contain a noun.
                # For now, let's be broad and generate all.
                # We could also check if the ngram itself starts/ends with a stopword if too noisy.
                current_ngram_phrase = "".join(ngram_tokens)
                # if current_ngram_phrase: # Ensure not empty string # Original check
                #     phrases.add(current_ngram_phrase.lower()) # All ngrams added as lowercase # Original add
                add_cleaned_phrase(phrases, current_ngram_phrase)
            else:
                break

        i += 1 # Always advance the main pointer
    return phrases

def _process_ner_results(doc: dict, ner_task_name: str) -> set[str]:
    """Extracts raw, lowercased entity text from NER results."""
    entities = set()
    ner_result = doc.get(ner_task_name)
    if ner_result and isinstance(ner_result, list):
        for sentence_entities in ner_result:
            if isinstance(sentence_entities, list):
                for entity_tuple in sentence_entities:
                    if isinstance(entity_tuple, (list, tuple)) and len(entity_tuple) > 0:
                        entity_text = str(entity_tuple[0]).strip()
                        if entity_text:
                            entities.add(entity_text.lower()) # Normalize to lowercase
                    else:
                        logger.warning(f"Malformed entity tuple found in NER results: {entity_tuple}")
            else:
                 logger.warning(f"Malformed sentence data found in NER results: {sentence_entities}")
    return entities

def _process_pos_results(doc: dict, tok_task_name: str, pos_task_name: str, pos_config: dict = DEFAULT_POS_CONFIG) -> set[str]:
    """Extracts lowercased noun phrases from POS results."""
    noun_phrases = set()
    tok_result = doc.get(tok_task_name)
    pos_result = doc.get(pos_task_name)

    if not (tok_result and pos_result and isinstance(tok_result, list) and isinstance(pos_result, list) and len(tok_result) == len(pos_result)):
        logger.warning(f"Missing or mismatched '{tok_task_name}' or '{pos_task_name}' results.")
        return noun_phrases

    for tokens, tags in zip(tok_result, pos_result):
        if isinstance(tokens, list) and isinstance(tags, list) and len(tokens) == len(tags):
            # _extract_noun_phrases_from_pos now returns lowercased phrases
            sentence_phrases = _extract_noun_phrases_from_pos(tokens, tags, pos_config)
            noun_phrases.update(sentence_phrases)
        else:
            logger.warning(f"Malformed token/tag data in sentence. Tokens: {tokens}, Tags: {tags}")
    return noun_phrases

def extract_concepts_hanlp(text: str) -> dict:
    """Extracts concepts using HanLPClient, filters by local Wikipedia titles, and extracts co-occurrence relationships."""
    if not HanLP_Client:
        logger.error("HanLPClient not initialized. Skipping concept extraction.")
        return {"concepts": [], "relationships": []}
    if not text.strip():
         logger.warning("Input text is empty or whitespace only. Skipping concept extraction.")
         return {"concepts": [], "relationships": []}

    logger.info(f"Starting HanLP concept extraction (NER+POS) for text length: {len(text)}. Will filter by local Wikipedia titles.")

    # --- Chunking Logic (remains the same) ---
    MAX_CHUNK_SIZE = 6000
    MIN_CHUNK_SIZE = 5
    chunks = []
    start_index = 0
    text_length = len(text)
    while start_index < text_length:
        end_index = min(start_index + MAX_CHUNK_SIZE, text_length)
        chunk = text[start_index:end_index]
        trimmed_chunk = chunk.strip()
        if trimmed_chunk and len(trimmed_chunk) >= MIN_CHUNK_SIZE:
            chunks.append(trimmed_chunk)
        elif chunk.strip():
            logger.debug(f"Skipping chunk shorter than {MIN_CHUNK_SIZE} chars: '{trimmed_chunk[:50]}...'")
        start_index = end_index
    # --- End Chunking Logic ---

    logger.info(f"Split text into {len(chunks)} chunks (target size ~{MAX_CHUNK_SIZE} chars) for HanLPClient processing.")

    all_ner_entities = set()
    all_pos_noun_phrases = set()
    processed_chunk_count = 0
    all_sentences_tok_output = []
    all_sentences_dep_output = []

    # --- Define API tasks and POS config --- 
    ner_task_name = 'ner/ontonotes'
    pos_task_name = 'pos/pku'
    tok_task_name = 'tok/coarse'
    dep_task_name = 'dep' # Added Dependency Parsing task
    api_tasks = [ner_task_name, tok_task_name, pos_task_name, dep_task_name] # Added dep_task_name
    skip_api_tasks = 'tok/fine' # Assuming tok/fine is not needed if we have tok/coarse for dep
    current_pos_config = DEFAULT_POS_CONFIG
    # --- End API tasks and POS config --- 

    for i, chunk in enumerate(chunks):
        logger.debug(f"Processing chunk {i+1}/{len(chunks)} via HanLPClient (Tasks: {api_tasks}), length: {len(chunk)}")
        current_chunk_doc = None # To store the HanLP parse result for the current chunk
        try:
            # --- Call HanLP API --- 
            current_chunk_doc = HanLP_Client.parse(text=chunk, tasks=api_tasks, skip_tasks=skip_api_tasks)
            logger.debug(f"HanLPClient response for chunk {i+1} received.")

            if i == 0 and logger.isEnabledFor(logging.DEBUG): # Only log for the first chunk
                logger.debug(f"--- Raw HanLP API Output for First Chunk ---")
                logger.debug(f"NER ('{ner_task_name}'): {current_chunk_doc.get(ner_task_name)}")
                logger.debug(f"TOK ('{tok_task_name}'): {current_chunk_doc.get(tok_task_name)}")
                logger.debug(f"POS ('{pos_task_name}'): {current_chunk_doc.get(pos_task_name)}")
                logger.debug(f"DEP ('{dep_task_name}'): {current_chunk_doc.get(dep_task_name)}")
                logger.debug(f"-------------------------------------------")

            # --- Process Results using Helper Functions --- 
            chunk_ner_entities = _process_ner_results(current_chunk_doc, ner_task_name)
            all_ner_entities.update(chunk_ner_entities)
            logger.debug(f"Processed {len(chunk_ner_entities)} NER entities from chunk {i+1}.")

            chunk_pos_phrases = _process_pos_results(current_chunk_doc, tok_task_name, pos_task_name, current_pos_config)
            all_pos_noun_phrases.update(chunk_pos_phrases)
            logger.debug(f"Processed {len(chunk_pos_phrases)} POS noun phrases from chunk {i+1}.")

            # Store tokenized sentences and DEP info for later relationship extraction
            if tok_task_name in current_chunk_doc and current_chunk_doc.get(tok_task_name):
                all_sentences_tok_output.extend(current_chunk_doc.get(tok_task_name))
            if dep_task_name in current_chunk_doc and current_chunk_doc.get(dep_task_name):
                all_sentences_dep_output.extend(current_chunk_doc.get(dep_task_name))
            
            # --- End Processing --- 
            processed_chunk_count += 1

        except Exception as e: # This is the except block for the try statement above
            logger.error(f"Error during HanLPClient processing for chunk {i+1} (length {len(chunk)}): {e}", exc_info=True)
            continue # This continue is for the loop `for i, chunk in enumerate(chunks):`
                 
    logger.info(f"Finished HanLPClient processing for {processed_chunk_count}/{len(chunks)} chunks.")
    logger.info(f"Total raw NER entities: {len(all_ner_entities)}, Total raw POS noun phrases: {len(all_pos_noun_phrases)}")

    # --- Combine and Filter Concepts --- 
    # Concepts are already lowercased from processing functions
    combined_concepts = all_ner_entities.union(all_pos_noun_phrases)
    logger.info(f"Total combined unique raw concepts before filtering: {len(combined_concepts)}")

    # --- Wikipedia Validation Step (New) ---
    concepts_to_filter_stage1 = set()
    # if ENABLE_WIKIPEDIA_CONCEPT_VALIDATION: # Removed this toggle, local filtering is now default if file loads
    if LOCAL_WIKIPEDIA_TITLES_SET: # Check if the local corpus was loaded successfully
        logger.info(f"Starting filtering of {len(combined_concepts)} raw concepts using local Wikipedia titles set ({len(LOCAL_WIKIPEDIA_TITLES_SET)} titles)...")
        # validated_count = 0 # Renamed
        # wiki_filtered_count = 0 # Renamed
        # processed_wiki_checks = 0 # Renamed
        
        concepts_passing_local_corpus_filter = set()
        local_corpus_filtered_out_count = 0

        # Iterate over a list copy for stable iteration if we were to modify combined_concepts directly (not needed here)
        combined_concepts_list = list(combined_concepts)
        for i, concept_text in enumerate(combined_concepts_list):
            # Log progress periodically to avoid flooding logs for many concepts
            if (i + 1) % 500 == 0 or i == len(combined_concepts_list) - 1 : # Log every 500 or on the last item
                logger.info(f"Local Wikipedia titles filtering progress: {i+1}/{len(combined_concepts_list)}")
            
            # Concept text is already lowercased. We should ideally load Wikipedia titles as lowercase too,
            # or normalize one of them here for comparison. Assuming titles in file are not necessarily lowercase.
            # For simplicity now, directly check. If titles are mixed case, this might miss some.
            # TODO: Consider normalizing LOCAL_WIKIPEDIA_TITLES_SET to lowercase upon loading for case-insensitive matching.
            if concept_text in LOCAL_WIKIPEDIA_TITLES_SET or concept_text.lower() in LOCAL_WIKIPEDIA_TITLES_SET: # Attempt case-insensitive
                concepts_passing_local_corpus_filter.add(concept_text) # Already lowercase
            else:
                logger.debug(f"[Local Corpus Filter] Removed '{concept_text}' (not found in local Wikipedia titles set).")
                local_corpus_filtered_out_count +=1
        
        logger.info(f"Finished local Wikipedia titles filtering. Kept: {len(concepts_passing_local_corpus_filter)}, Removed: {local_corpus_filtered_out_count}.")
        concepts_to_filter_stage1 = concepts_passing_local_corpus_filter
    else:
        logger.warning("Local Wikipedia titles set is empty or not loaded. Skipping filtering by local corpus.")
        concepts_to_filter_stage1 = combined_concepts
    # --- End Wikipedia Validation Step ---

    # Log a sample of raw concepts for debugging
    # if logger.isEnabledFor(logging.DEBUG) and not ENABLE_WIKIPEDIA_CONCEPT_VALIDATION: # Only log if wiki validation didn't happen
    #     sample_raw_concepts = sorted(list(concepts_to_filter_stage1))[:100]
    #     logger.debug(f"Sample of concepts entering Stage 1 filtering (Wikipedia validation skipped): {sample_raw_concepts}")
    # elif logger.isEnabledFor(logging.DEBUG) and ENABLE_WIKIPEDIA_CONCEPT_VALIDATION:
    #     sample_validated_concepts = sorted(list(concepts_to_filter_stage1))[:100]
    #     logger.debug(f"Sample of concepts entering Stage 1 filtering (after Wikipedia validation): {sample_validated_concepts}")
    if logger.isEnabledFor(logging.DEBUG):
        sample_concepts_after_local_corpus_filter = sorted(list(concepts_to_filter_stage1))[:100]
        if LOCAL_WIKIPEDIA_TITLES_SET:
            logger.debug(f"Sample of concepts entering Stage 1 filtering (after local Wikipedia titles filter): {sample_concepts_after_local_corpus_filter}")
        else:
            logger.debug(f"Sample of concepts entering Stage 1 filtering (local Wikipedia titles filter skipped): {sample_concepts_after_local_corpus_filter}")


    # --- Filtering Stage 1: Basic Format, Length, Stopwords (Simplified for Debugging) ---
    filtered_concepts_stage1 = set()
    # numeric_punct_pattern definition is removed as per user's previous file state

    min_concept_len = 3 # Increased min length
    max_concept_len = 25
    current_stopwords = DEFAULT_STOPWORDS # Using the minimal stopwords

    logger.debug("--- Filtering Stage 1: Basic format, length, minimal stopwords --- ") # Log message updated
    for concept_text in concepts_to_filter_stage1:
        # Stopword check (using minimal list)
        if concept_text in current_stopwords:
            logger.debug(f"[Filter Stage 1] Removed (Minimal Stopword): '{concept_text}'")
            continue
                
        # Basic length check
        if not (min_concept_len <= len(concept_text) <= max_concept_len):
            logger.debug(f"[Filter Stage 1] Removed (Length {len(concept_text)}): '{concept_text}'")
            continue
                
        filtered_concepts_stage1.add(concept_text)

    logger.info(f"Concepts after Stage 1 filtering (Expanded Rules): {len(filtered_concepts_stage1)}")

    # --- Filtering Stage 2: Subphrase Removal (Temporarily Disabled for Debugging) --- 
    # logger.debug("--- Filtering Stage 2: Removing subphrases --- ")
    # # Sort by length descending to check longer phrases first
    # sorted_concepts = sorted(list(filtered_concepts_stage1), key=len, reverse=True)
    # final_concepts_set = set()
    # for concept in sorted_concepts:
    #     is_subphrase = False
    #     # Check if this concept is a subphrase of an already added longer concept
    #     for existing in final_concepts_set:
    #         if concept != existing and concept in existing:
    #             # Basic substring check, might need refinement (e.g., word boundaries)
    #             is_subphrase = True
    #             logger.debug(f"Removing subphrase '{concept}' because it's part of '{existing}'")
    #             break
    #     if not is_subphrase:
    #         final_concepts_set.add(concept)
    # --- End Subphrase Removal --- 

    # --- Use results from Stage 1 directly when Stage 2 is disabled --- 
    final_concepts_set = filtered_concepts_stage1
    # --- End Use results from Stage 1 --- 

    logger.info(f"Found {len(final_concepts_set)} unique concepts after all filtering (Subphrase removal disabled).")
    if logger.isEnabledFor(logging.DEBUG):
        log_limit = 100
        final_list = sorted(list(final_concepts_set))
        logger.debug(f"Final Concepts (showing up to {log_limit}): {final_list[:log_limit]}{'...' if len(final_list) > log_limit else ''}")

    concept_objects = [Concept(term=term.strip()) for term in sorted(list(final_concepts_set))] # Ensure stripped term
    
    # --- New DEP-based relationship extraction --- 
    # Create a combined "doc-like" structure for _extract_relations_from_dep
    aggregated_doc_for_dep = {
        tok_task_name: all_sentences_tok_output,
        dep_task_name: all_sentences_dep_output
    }

    if final_concepts_set and all_sentences_tok_output and all_sentences_dep_output:
        logger.info(f"Starting DEP-based relationship extraction for {len(final_concepts_set)} concepts from {len(all_sentences_tok_output)} sentences...")
        # Pass the aggregated data, not the last chunk's doc
        extracted_dep_relations = _extract_relations_from_dep(aggregated_doc_for_dep, final_concepts_set, tok_task_name, dep_task_name)
        relationship_objects = [Relationship(source=r[0], target=r[1], label=r[2] if len(r) > 2 else None) for r in sorted(list(extracted_dep_relations))]
        logger.info(f"Created {len(relationship_objects)} Relationship objects from DEP extraction.")
    else:
        logger.warning("Skipping DEP-based relationship extraction: no final concepts or insufficient HanLP tok/dep data.")
        relationship_objects = []
    # --- End Relationship Extraction ---

    return {"concepts": concept_objects, "relationships": relationship_objects}

# --- Modified function to use OwnThink API ---
def get_ownthink_definition(term: str) -> str | None:
    """Fetches a brief definition for a term from the OwnThink Knowledge Graph API."""
    logger.info(f"Attempting to fetch definition for term: '{term}' from OwnThink API.")
    
    api_url = "https://api.ownthink.com/kg/knowledge?entity" 
    params = {"entity": term}
    definition = None
    
    try:
        # Use POST method as shown in 1.py, sending term in JSON payload
        response = requests.post(api_url, json=params, timeout=10) # Added timeout
        
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            if data.get("message") == "success" and "data" in data:
                entity_data = data["data"]
                if "desc" in entity_data and entity_data["desc"]:
                    definition = entity_data["desc"]
                    logger.info(f"Successfully fetched definition for '{term}' from OwnThink: {definition[:50]}...") # Log first 50 chars
                else:
                    logger.warning(f"OwnThink API success for '{term}', but 'desc' field missing or empty in data: {entity_data}")
            elif data.get("message"):
                 logger.warning(f"OwnThink API returned non-success message for '{term}': {data.get('message')}")
            else:
                logger.warning(f"OwnThink API success for '{term}', but response format unexpected: {data}")
        else:
            logger.error(f"OwnThink API request failed for '{term}'. Status Code: {response.status_code}, Response: {response.text[:200]}") # Log first 200 chars of error response

    except requests.exceptions.RequestException as e:
        # Catch potential network errors, timeouts, etc.
        logger.error(f"An unexpected error occurred fetching definition for '{term}' from OwnThink API: {e}", exc_info=True)
    except Exception as e:
        # Catch other potential errors (e.g., JSON decoding)
        logger.error(f"An unexpected error occurred processing OwnThink API response for '{term}': {e}", exc_info=True)

    return definition
# --- End Modified function ---

# Constants for difficulty analysis weights
WEIGHT_TERM_DENSITY = 0.30
WEIGHT_FORMULA_COMPLEXITY = 0.25
WEIGHT_FIGURE_TABLE = 0.20
WEIGHT_CITATION_DENSITY = 0.15
WEIGHT_LONG_SENTENCE = 0.10

# Other existing constants for thresholds
LONG_SENTENCE_CHAR_THRESHOLD = 120

# New thresholds for formula complexity (tiered scoring)
FORMULA_COUNT_THRESHOLD_LOW = 1
FORMULA_COUNT_THRESHOLD_HIGH = 3 # Stricter high threshold
FORMULA_LENGTH_THRESHOLD_LOW = 20  # Total characters for low complexity
FORMULA_LENGTH_THRESHOLD_HIGH = 80 # Stricter high threshold for total length

def _analyze_segment_difficulty(
    segment_text: str,
    concepts_on_document: set[str],
    segment_id: str,
    page_index: int,
    block_index_on_page: int,
    figure_count_on_page: int, # Changed from page_has_figures
    table_count_on_page: int    # Changed from page_has_tables
) -> SegmentDifficultyMarker:
    """Analyzes a single text segment (block) for cognitive difficulty indicators using a weighted scoring model."""
    raw_scores = {
        "term_density": 0.0,
        "formula_complexity": 0.0,
        "figure_table": 0.0,
        "citation_density": 0.0,
        "long_sentence": 0.0
    }
    reasons = []
    current_segment_text = segment_text if isinstance(segment_text, str) else ""
    segment_text_lower = current_segment_text.lower().strip()
    text_preview = current_segment_text.strip()[:100]

    if not segment_text_lower:
        return SegmentDifficultyMarker(
            segment_id=segment_id, page_index=page_index, block_index_on_page=block_index_on_page,
            text_preview=text_preview, score=0.0, reasons=[]
        )

    # 1. Academic Term Density
    concepts_found_in_segment = {c for c in concepts_on_document if c in segment_text_lower}
    term_count = len(concepts_found_in_segment)
    raw_scores["term_density"] = float(term_count)
    if term_count > 0:
        reasons.append(f"term_density_segment ({term_count})")

    # 2. Formula Complexity
    formula_pattern_str = r"([a-zA-Z]?\s*[+\-\*/=<>≤≥∈∑∫∏√^]\s*[a-zA-Z\d])|(\b(alpha|beta|gamma|delta|epsilon|zeta|eta|theta|iota|kappa|lambda|mu|nu|xi|omicron|pi|rho|sigma|tau|upsilon|phi|chi|psi|omega)\b)|([\d.\s]*[+\-\*/=<>≤≥∈∑∫∏√^][\d.\s]+)|(\([+\-\*/=<>≤≥∈∑∫∏√^]+\))|(\[[\w\s+\-\*/=<>≤≥∈∑∫∏√^]+\])|(\{[\w\s+\-\*/=<>≤≥∈∑∫∏√^]+\})"
    formula_matches_iter = list(re.finditer(formula_pattern_str, segment_text_lower, re.VERBOSE | re.IGNORECASE))
    formula_count = len(formula_matches_iter)
    total_formula_length = sum(match.end() - match.start() for match in formula_matches_iter)
    
    # Tiered scoring for formulas
    raw_scores["formula_complexity"] = 0.0
    has_any_formula = formula_count > 0 or total_formula_length > 0
    is_high_complexity = formula_count >= FORMULA_COUNT_THRESHOLD_HIGH or total_formula_length >= FORMULA_LENGTH_THRESHOLD_HIGH
    is_medium_complexity = formula_count >= FORMULA_COUNT_THRESHOLD_LOW or total_formula_length >= FORMULA_LENGTH_THRESHOLD_LOW

    if is_high_complexity:
        raw_scores["formula_complexity"] = 1.0
    elif is_medium_complexity:
        raw_scores["formula_complexity"] = 0.6 # Tier for medium complexity
    elif has_any_formula:
        raw_scores["formula_complexity"] = 0.2 # Tier for low/any complexity

    if has_any_formula:
        reasons.append(f"formulas_in_segment (count: {formula_count}, length: {total_formula_length})")

    # 3. Figure/Table Count on Page
    raw_scores["figure_table"] = float(figure_count_on_page) + float(table_count_on_page)
    if figure_count_on_page > 0:
        reasons.append(f"figures_on_page ({figure_count_on_page})")
    if table_count_on_page > 0:
        reasons.append(f"tables_on_page ({table_count_on_page})")

    # 4. Citation Density
    citation_pattern_str = r"(\[\d+\])|(\([^)]*\d{4}[^(]*\))|(\b[A-Za-z]+\s+et\s+al\.,?\s+\d{4})"
    citation_count = len(list(re.finditer(citation_pattern_str, current_segment_text)))
    raw_scores["citation_density"] = float(citation_count)
    if citation_count > 0:
        reasons.append(f"citations_in_segment ({citation_count})")

    # 5. Long Sentence Detection
    sentence_parts = re.split(r'([。？！；!?;]+)', current_segment_text)
    sentences = []
    current_sentence_agg = "" # Renamed to avoid conflict
    for part in sentence_parts:
        if not part: continue
        current_sentence_agg += part
        if re.match(r'^[。？！；!?;]+$', part.strip()): 
            if current_sentence_agg.strip():
                sentences.append(current_sentence_agg.strip())
            current_sentence_agg = ""
    if current_sentence_agg.strip():
        sentences.append(current_sentence_agg.strip())
    
    sentences = [s for s in sentences if len(s) > 5] 
    long_sentence_count = 0
    for sent in sentences:
        if len(sent) > LONG_SENTENCE_CHAR_THRESHOLD:
            long_sentence_count += 1
    
    raw_scores["long_sentence"] = float(long_sentence_count)
    if long_sentence_count > 0:
        reasons.append(f"long_sentences_in_segment ({long_sentence_count})")

    # Calculate final weighted score
    final_score = (
        raw_scores["term_density"] * WEIGHT_TERM_DENSITY +
        raw_scores["formula_complexity"] * WEIGHT_FORMULA_COMPLEXITY +
        raw_scores["figure_table"] * WEIGHT_FIGURE_TABLE +
        raw_scores["citation_density"] * WEIGHT_CITATION_DENSITY +
        raw_scores["long_sentence"] * WEIGHT_LONG_SENTENCE
    )

    logger.debug(f"Segment: {segment_id}, Page: {page_index}, Block: {block_index_on_page}")
    logger.debug(f"  Raw Scores: {raw_scores}")
    logger.debug(f"  Weighted Final Score: {final_score:.3f}")
    logger.debug(f"  Reasons: {reasons}")

    return SegmentDifficultyMarker(
        segment_id=segment_id, page_index=page_index, block_index_on_page=block_index_on_page,
        text_preview=text_preview, score=round(final_score, 3), reasons=sorted(list(set(reasons))) # Round score
    )

# --- FastAPI Application Instance ---
app = FastAPI(title="MindFlow Reader Backend API (HanLP + OwnThink)", version="0.1.2")

# --- CORS Middleware Configuration ---
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Endpoints ---

@app.post("/extract-concepts", response_model=ConceptListResponse,
          summary="Extract Concepts from Text (HanLP)",
          description="Receives raw text and returns a list of extracted concepts using HanLP NER.")
async def process_text_for_concepts(request: TextProcessingRequest):
    """Processes raw input text to extract key concepts using HanLP."""
    logger.info(f"Received request for /extract-concepts. Text length: {len(request.text)}")
    if not request.text:
        logger.warning("Request to /extract-concepts with empty text.")
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    extraction_result = extract_concepts_hanlp(request.text)
    logger.info(f"Returning {len(extraction_result['concepts'])} concepts for text request.")
    return ConceptListResponse(concepts=extraction_result['concepts'])

@app.post("/upload-and-extract", response_model=DocumentUploadResponse,
          summary="Upload PDF and Extract Concepts (HanLP)",
          description="Accepts PDF upload, extracts text, returns doc info with concepts using HanLP NER, and updates global graph.")
async def upload_pdf_and_extract_concepts(file: UploadFile = File(..., description="The PDF file to process.")):
    """Handles PDF upload, text extraction, HanLP concept identification, and updates the mock global knowledge graph."""
    logger.info(f"Received request for /upload-and-extract. Filename: '{file.filename}'")

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        logger.warning(f"Invalid file upload attempt: Filename '{file.filename}' is not a PDF.")
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF file.")

    doc_id = str(uuid.uuid4()) # Generate a unique ID for the document early

    try:
        pdf_bytes = await file.read()
        logger.info(f"Read {len(pdf_bytes)} bytes from uploaded PDF: '{file.filename}'")

        doc = fitz.open(stream=io.BytesIO(pdf_bytes), filetype="pdf")
        page_count = doc.page_count # Get page count
        logger.info(f"Opened PDF '{file.filename}' with {page_count} pages.")

        # Extract title from metadata, fallback to filename without extension
        pdf_title = doc.metadata.get('title', None)
        if not pdf_title or pdf_title.strip() == '':
             # Use filename without extension as fallback
             pdf_title = Path(file.filename).stem 
        logger.info(f"Using title: '{pdf_title}' for document '{file.filename}' (ID: {doc_id})")

        # --- Update Mock Global Store with Document Info ---
        global_knowledge_graph["documents"][doc_id] = {"id": doc_id, "title": pdf_title}
        # --- End Update ---

        # Extract text from all pages AND store page-wise text
        # full_text = "\n".join([page.get_text("text") for page in doc]) # Old way
        page_texts = [page.get_text("text") for page in doc]
        full_text = "\n".join(page_texts)
        doc.close()
        logger.info(f"Extracted total text length: {len(full_text)} from '{file.filename}' ({len(page_texts)} pages)")

        if not full_text.strip():
            logger.warning(f"No text could be extracted from the PDF: '{file.filename}'. Raising error.")
            raise HTTPException(status_code=422, detail="No text content could be extracted from the PDF.")

        # Use the HanLP helper function to extract concepts and relationships from the *full text*
        extraction_result = extract_concepts_hanlp(full_text)
        concepts_raw = extraction_result.get("concepts", []) # List[Concept]
        relationships_raw = extraction_result.get("relationships", []) # List[Relationship]
        final_concepts_set_from_hanlp = {c.term for c in concepts_raw} # Get the final set for page analysis

        # --- Update Mock Global Store with Concepts and Relationships ---
        for concept_obj in concepts_raw:
            term = concept_obj.term
            if term not in global_knowledge_graph["nodes"]:
                global_knowledge_graph["nodes"][term] = {"name": term, "document_ids": set()}
            global_knowledge_graph["nodes"][term]["document_ids"].add(doc_id)
        
        for rel_obj in relationships_raw:
            # Store edges with document_id to know their origin for global graph representation
            edge_tuple = (rel_obj.source, rel_obj.target, rel_obj.label, doc_id)
            global_knowledge_graph["edges"].add(edge_tuple)
        logger.info(f"Updated mock global knowledge graph with {len(concepts_raw)} concepts and {len(relationships_raw)} relationships from document ID {doc_id}.")
        # --- End Update ---

        # *** Analyze difficulty segment by segment (New Approach) ***
        difficulty_markers_list: list[SegmentDifficultyMarker] = []
        if final_concepts_set_from_hanlp: # Only analyze if we have concepts
            logger.info(f"Starting segment-by-segment difficulty analysis for {len(page_texts)} pages...")
            # Re-open the document to iterate through pages and blocks
            doc_for_analysis = fitz.open(stream=io.BytesIO(pdf_bytes), filetype="pdf")
            for page_idx, page_obj in enumerate(doc_for_analysis):
                # Pre-calculate figure/table presence for the page
                figure_list_on_page = page_obj.get_images(full=True)
                figure_count_on_page = len(figure_list_on_page)
                # Check tables robustly
                try:
                    table_finder = page_obj.find_tables()
                    table_count_on_page = len(table_finder.tables) if table_finder and table_finder.tables else 0
                except Exception as table_exc:
                    logger.warning(f"Error checking tables on page {page_idx}: {table_exc}")
                    table_count_on_page = 0

                blocks = page_obj.get_text("blocks", sort=True)
                for block_idx, block_data in enumerate(blocks):
                    # block_data format: (x0, y0, x1, y1, text, block_no, block_type)
                    if len(block_data) < 7: continue # Ensure valid block data
                    block_text = block_data[4]
                    block_type = block_data[6]

                    if block_type != 0: # 0 indicates a text block
                        continue
                    if not block_text or not block_text.strip():
                        continue
                    
                    segment_id = f"p{page_idx}_b{block_idx}"
                    # text_preview = block_text.strip()[:100] # Preview generated within analysis function
                    
                    # --- Call the refactored analysis function (Uncommented) ---
                    try:
                        marker = _analyze_segment_difficulty(
                            segment_text=block_text,
                            concepts_on_document=final_concepts_set_from_hanlp,
                            segment_id=segment_id,
                            page_index=page_idx,
                            block_index_on_page=block_idx,
                            figure_count_on_page=figure_count_on_page,
                            table_count_on_page=table_count_on_page
                        )
                        if marker and marker.score > 0: # Only add markers with a non-zero score
                            difficulty_markers_list.append(marker)
                    except NameError: # If the function is not defined due to some unexpected issue
                         logger.error("_analyze_segment_difficulty is not defined. Skipping analysis for this segment.")
                         # Optional: break the inner loop or the outer loop if analysis is critical
                         # For now, just log and continue processing other blocks/pages
                    except Exception as analysis_exc:
                         logger.error(f"Error analyzing segment {segment_id}: {analysis_exc}", exc_info=True)
                    # ---------------------------------------------------------------------
            
            doc_for_analysis.close() # Close the temporarily opened doc
            logger.info(f"Finished segment difficulty analysis. Found {len(difficulty_markers_list)} segments with non-zero difficulty scores.")
        else:
            logger.warning("Skipping segment difficulty analysis as no concepts were extracted.")
        # *** End difficulty analysis ***
        
        # Format concepts for frontend (this part is for the immediate response of this endpoint)
        concepts_for_frontend = [{'term': c.term, 'definition': None} for c in concepts_raw]

        # The doc_id was generated earlier
    
        # Return the new response structure, fixing previous indentation
        return {
            "id": doc_id,
            "title": pdf_title,
            "concepts": concepts_for_frontend, # Concepts specific to this doc for immediate display
            "relationships": relationships_raw, # Relationships specific to this doc
            "difficulty_markers": difficulty_markers_list # Include the generated markers
        }

    except Exception as e:
        # This will now catch PyMuPDF errors as well as others
        logger.error(f"Unexpected error during PDF processing or concept extraction for '{file.filename}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during file processing.")
    finally:
        # Ensure the file handle is closed by FastAPI/Starlette
        await file.close()
        logger.debug(f"Closed file handle for '{file.filename}'")

@app.get("/global-graph", response_model=GlobalGraphResponse)
async def get_global_graph_data(document_ids: Optional[List[str]] = Query(None)):
    logger.info(f"Received request for /global-graph. Filter by document_ids: {document_ids}")
    
    nodes_response = []
    links_tuples_set = set() # Stores tuples like (source, target, label, document_id)
    
    doc_ids_filter_set = set(document_ids) if document_ids else None

    filtered_documents_for_categories = {}
    if doc_ids_filter_set:
        for doc_id, doc_data in global_knowledge_graph["documents"].items():
            if doc_id in doc_ids_filter_set:
                filtered_documents_for_categories[doc_id] = doc_data
    else:
        filtered_documents_for_categories = global_knowledge_graph["documents"]
    
    doc_id_to_filtered_index = {doc_id: i for i, doc_id in enumerate(filtered_documents_for_categories.keys())}
    nodes_to_include_ids = set()
    temp_links_tuples = [] # Store tuples here first

    if doc_ids_filter_set:
        for s, t, lbl, doc_id_of_link in global_knowledge_graph["edges"]:
            if doc_id_of_link in doc_ids_filter_set:
                # 添加元组到临时的列表
                temp_links_tuples.append((s, t, lbl, doc_id_of_link))
                nodes_to_include_ids.add(s)
                nodes_to_include_ids.add(t)
    else:
        for s, t, lbl, doc_id_of_link in global_knowledge_graph["edges"]:
            # 添加元组到临时的列表
            temp_links_tuples.append((s, t, lbl, doc_id_of_link))
            nodes_to_include_ids.add(s)
            nodes_to_include_ids.add(t)
    
    # 将唯一的元组添加到 links_tuples_set
    for s, t, lbl, doc_id_of_link in temp_links_tuples:
         links_tuples_set.add((s, t, lbl, doc_id_of_link)) # Add tuple to the set

    # 过滤节点 (这部分逻辑看起来是正确的，继续使用 nodes_to_include_ids)
    for term, node_data in global_knowledge_graph["nodes"].items():
        if doc_ids_filter_set:
            if term in nodes_to_include_ids and any(doc_id_node_belongs_to in doc_ids_filter_set for doc_id_node_belongs_to in node_data["document_ids"]):
                primary_doc_for_node_in_filter = next((doc_id for doc_id in node_data["document_ids"] if doc_id in doc_ids_filter_set), None)
                category_idx = doc_id_to_filtered_index.get(primary_doc_for_node_in_filter) if primary_doc_for_node_in_filter else None
                nodes_response.append(
                    GlobalGraphResponseNode(
                        id=term, 
                        name=term, 
                        document_ids=[doc_id for doc_id in node_data["document_ids"] if doc_id in doc_ids_filter_set],
                        category_index=category_idx
                    )
                )
        else: 
            if term in nodes_to_include_ids:
                primary_doc_id = list(node_data["document_ids"])[0] if node_data["document_ids"] else None
                category_idx = doc_id_to_filtered_index.get(primary_doc_id) if primary_doc_id else None
                nodes_response.append(
                    GlobalGraphResponseNode(
                        id=term, 
                        name=term, 
                        document_ids=list(node_data["document_ids"]),
                        category_index=category_idx
                    )
                )
    
    # 将集合中的元组转换回 GlobalGraphResponseLink 对象列表
    final_links_response = [
        GlobalGraphResponseLink(source=s, target=t, label=lbl, document_id=doc_id_of_link)
        for s, t, lbl, doc_id_of_link in links_tuples_set
    ]
    
    final_documents_response = [
        GlobalGraphResponseDocument(id=doc_data["id"], title=doc_data["title"])
        for doc_data in filtered_documents_for_categories.values()
    ]

    logger.info(f"Returning filtered global graph with {len(nodes_response)} nodes, {len(final_links_response)} links, and {len(final_documents_response)} documents.")
    return GlobalGraphResponse(
        nodes=nodes_response, 
        links=final_links_response, 
        documents=final_documents_response
    )

@app.get("/definition/{term}", response_model=DefinitionResponse,
         summary="Get Term Definition (OwnThink)", # Updated summary
         description="Retrieves a definition for the given term from the OwnThink Knowledge Graph API.") # Updated description
async def get_definition(term: str):
    """Fetches a definition for a given term using OwnThink API."""
    logger.info(f"Received request for /definition/{term}")
    if not term:
        raise HTTPException(status_code=400, detail="Term cannot be empty")

    # URL Decode the term
    # No need for urllib.parse if only used for wikipedia previously
    # Ensure you handle potential encoding issues if terms might contain special chars
    decoded_term = term # Assuming basic URL decoding is handled by FastAPI path param

    logger.info(f"Fetching definition for decoded term: '{decoded_term}' using OwnThink")

    # Call the new helper function
    definition = get_ownthink_definition(decoded_term) 

    # Return 200 OK with the definition (or null if not found/error)
    return DefinitionResponse(term=decoded_term, definition=definition)

@app.get("/", include_in_schema=False) # Hide from OpenAPI docs if desired
async def read_root():
    """Basic root endpoint indicating the API is running."""
    return {"message": "MindFlow Reader Backend API is running."}

# --- Optional: Uvicorn run command for local development ---
# Note: Typically run from the command line: uvicorn main:app --reload
# if __name__ == "__main__":
#     import uvicorn
#     logger.info("Starting Uvicorn server directly from script...")
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 