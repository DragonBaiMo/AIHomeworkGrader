<script setup lang="ts">
import { computed, ref } from "vue";
import type { GradeConfigPayload, GradeResponse, TemplateOption } from "@/api/types";

const props = defineProps<{
  config: GradeConfigPayload;
  templates: TemplateOption[];
  loading: boolean;
  result: GradeResponse | null;
  statusText: string;
}>();

const emit = defineEmits<{
  (e: "submit", files: File[]): void;
  (e: "request-settings"): void;
  (e: "update:config", payload: Partial<GradeConfigPayload>): void;
}>();

const files = ref<File[]>([]);
const dragOver = ref(false);
const hint = ref<string>("");
const resultFilter = ref<"all" | "success" | "fail">("all");
const resultQuery = ref<string>("");
const expandedRows = ref<Set<string>>(new Set());

// --- Tech Dropdown Logic ---
const isTemplateOpen = ref(false);
const currentTemplateLabel = computed(() => 
  props.templates.find(t => t.value === props.config.template)?.label || props.config.template
);

function selectTemplate(val: string) {
  updateConfigField('template', val);
  isTemplateOpen.value = false;
}

// Close dropdown when clicking outside (Simple overlay approach)
function closeDropdown() {
  isTemplateOpen.value = false;
}

const Icons = {
  Upload: `<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>`,
  Doc: `<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>`,
  Check: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`,
  Download: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>`,
  Alert: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`,
  ChevronDown: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>`,
  Search: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>`
};

const fileSummary = computed(() => {
  if (!files.value.length) return "";
  const total = files.value.length;
  const sizeMB = files.value.reduce((acc, cur) => acc + cur.size, 0) / 1024 / 1024;
  return `${total} 个文件 (${sizeMB.toFixed(1)} MB)`;
});

const filteredItems = computed(() => {
  const items = props.result?.items || [];
  const query = (resultQuery.value || "").trim();
  return items.filter((item) => {
    if (resultFilter.value === "success" && item.status !== "成功") return false;
    if (resultFilter.value === "fail" && item.status === "成功") return false;
    if (!query) return true;
    const hay = `${item.file_name} ${item.student_id || ""} ${item.student_name || ""}`.toLowerCase();
    return hay.includes(query.toLowerCase());
  });
});

const parsedFilteredItems = computed(() => {
  return filteredItems.value.map((item) => {
    let detail: any = {};
    try {
      detail = item.detail_json ? JSON.parse(item.detail_json) : {};
    } catch (e) { /* ignore */ }
    
    return {
      ...item,
      rubric_items: detail.rubric_items || [],
      feedback: detail.feedback || item.comment || "",
      error_message: item.error_message || detail.error,
      display_score: typeof detail.total_score === 'number' ? detail.total_score : item.score
    };
  });
});

function getScoreClass(score: number | null | undefined) {
  if (score === null || score === undefined) return "";
  if (score >= 90) return "score-high";
  if (score >= 60) return "score-mid";
  return "score-low";
}

function toggleRow(key: string) {
  const set = expandedRows.value;
  if (set.has(key)) set.delete(key);
  else set.add(key);
  expandedRows.value = new Set(set);
}

const SUPPORTED_EXTENSIONS = [".docx", ".md", ".markdown", ".txt"] as const;

function isSupportedFileName(fileName: string): boolean {
  const lower = fileName.toLowerCase();
  return SUPPORTED_EXTENSIONS.some((ext) => lower.endsWith(ext));
}

function updateFiles(list: FileList | File[]) {
  files.value = Array.from(list).filter((file) => isSupportedFileName(file.name));
  if (!files.value.length) {
    hint.value = "仅支持 .docx / .md / .markdown / .txt";
    return;
  }
  hint.value = "";
}

function onFileChange(event: Event) {
  const target = event.target as HTMLInputElement;
  if (target.files) updateFiles(target.files);
}

function onDrop(event: DragEvent) {
  event.preventDefault();
  dragOver.value = false;
  if (event.dataTransfer?.files) updateFiles(event.dataTransfer.files);
}

function handleSubmit() {
  if (!files.value.length) return;
  if (!props.config.mock && !props.config.apiUrl) {
    emit("request-settings");
    return;
  }
  emit("submit", files.value);
}

function updateConfigField<T extends keyof GradeConfigPayload>(key: T, value: GradeConfigPayload[T]) {
  emit("update:config", { [key]: value } as Partial<GradeConfigPayload>);
}
</script>

<template>
  <div class="workspace-layout">
    <!-- Header: Command Center -->
    <header class="workspace-header">
      <div class="header-titles">
        <h1 class="page-title">智能批改台</h1>
        <p class="page-subtitle">AI Automated Assessment System</p>
      </div>

      <div class="command-bar">
        <!-- Template Selector -->
        <div class="command-group">
          <label class="command-label">评估模板</label>
          <div class="bento-select" :class="{ active: isTemplateOpen }">
            <button 
              class="select-trigger" 
              @click="isTemplateOpen = !isTemplateOpen"
            >
              <span class="selected-text">{{ currentTemplateLabel }}</span>
              <span class="trigger-icon" v-html="Icons.ChevronDown"></span>
            </button>

            <Transition name="pop-scale">
              <div v-if="isTemplateOpen" class="bento-dropdown">
                <div 
                  v-for="t in templates" 
                  :key="t.value" 
                  class="dropdown-option"
                  :class="{ selected: t.value === config.template }"
                  @click="selectTemplate(t.value)"
                >
                  <span class="option-label">{{ t.label }}</span>
                  <span v-if="t.value === config.template" class="check-mark" v-html="Icons.Check"></span>
                </div>
              </div>
            </Transition>
            
            <!-- Backdrop -->
            <div v-if="isTemplateOpen" class="backdrop-click" @click="closeDropdown"></div>
          </div>
        </div>

        <div class="divider-vertical"></div>

        <!-- Mode Toggle -->
        <div class="command-group horizontal">
          <label class="switch-container">
            <input 
              type="checkbox" 
              class="sr-only"
              :checked="config.mock"
              @change="updateConfigField('mock', ($event.target as HTMLInputElement).checked)"
            />
            <div class="switch-track">
              <div class="switch-thumb"></div>
            </div>
          </label>
          <span class="command-label clickable" @click="updateConfigField('mock', !config.mock)">模拟模式</span>
        </div>
      </div>
    </header>

    <!-- Drop Zone: Energy Field -->
    <section class="upload-section">
      <div
        class="drop-zone-card"
        :class="{ 
          'is-dragover': dragOver, 
          'has-files': files.length > 0,
          'is-processing': loading 
        }"
        @dragover.prevent="dragOver = true"
        @dragleave="dragOver = false"
        @drop="onDrop"
      >
        <div class="zone-content">
          <div class="visual-anchor">
            <div class="ripple-ring r1"></div>
            <div class="ripple-ring r2"></div>
            <div class="icon-stage">
              <div v-if="loading" class="loader-spinner"></div>
              <div v-else-if="files.length" v-html="Icons.Doc" class="stage-icon file"></div>
              <div v-else v-html="Icons.Upload" class="stage-icon"></div>
            </div>
          </div>

          <div class="text-anchor">
            <h3 v-if="loading" class="zone-title">正在深度分析...</h3>
            <h3 v-else-if="files.length" class="zone-title highlight">{{ fileSummary }}</h3>
             <h3 v-else class="zone-title">拖入作业文档</h3>
             
            <p v-if="!loading" class="zone-subtitle">支持 .docx / .md / .markdown / .txt</p>
            <p v-if="hint" class="zone-error">{{ hint }}</p>
          </div>

          <div class="action-anchor" v-if="!loading">
            <label v-if="!files.length" class="bento-btn primary">
              <span>选择文件</span>
              <input type="file" accept=".docx,.md,.markdown,.txt" multiple hidden @change="onFileChange" />
            </label>
            
            <div v-else class="btn-group">
              <button class="bento-btn ghost" @click="files = []">清空</button>
              <button class="bento-btn primary" @click="handleSubmit">开始批改</button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Results: Smart Dashboard -->
    <Transition name="fade-slide">
      <section v-if="result" class="results-dashboard">
        
        <!-- Stats Bento -->
        <div class="stats-bento">
          <div class="bento-card stat-total">
            <span class="bento-label">总文件</span>
            <span class="bento-value">{{ result.total_files }}</span>
          </div>
          <div class="bento-card stat-success">
            <span class="bento-label">成功</span>
            <span class="bento-value">{{ result.success_count }}</span>
          </div>
          <div class="bento-card stat-error" :class="{ 'has-error': result.error_count > 0 }">
            <span class="bento-label">异常</span>
            <span class="bento-value">{{ result.error_count }}</span>
          </div>
          <div class="bento-card stat-avg">
            <span class="bento-label">平均分</span>
            <span class="bento-value">{{ result.average_score ? result.average_score.toFixed(1) : '-' }}</span>
          </div>
          <div class="bento-card action-cell">
             <div class="action-stack">
                <button class="bento-icon-btn" title="导出 CSV">
                   <span v-html="Icons.Download"></span>
                </button>
             </div>
          </div>
        </div>

        <!-- Result List Container -->
        <div class="list-module">
          <div class="module-header">
            <div class="filter-pill-group">
              <button 
                v-for="f in ['all', 'success', 'fail']" 
                :key="f"
                class="filter-pill"
                :class="{ active: resultFilter === f }"
                @click="resultFilter = f as any"
              >
                {{ f === 'all' ? '全部' : f === 'success' ? '成功' : '异常' }}
              </button>
            </div>
            
            <div class="search-input-wrapper">
              <span class="search-icon" v-html="Icons.Search"></span>
              <input 
                type="text" 
                v-model="resultQuery" 
                placeholder="搜索学生或文件名..." 
                class="clean-input"
              />
            </div>
          </div>

          <div class="module-body custom-scrollbar">
            <!-- Table Header -->
            <div class="table-header">
              <div class="th col-file">文件名称</div>
              <div class="th col-id">学号</div>
              <div class="th col-name">姓名</div>
              <div class="th col-score">成绩</div>
              <div class="th col-status">状态</div>
              <div class="th col-action">操作</div>
            </div>

            <!-- List Items -->
            <div class="table-rows">
              <div 
                v-for="item in parsedFilteredItems" 
                :key="item.file_name"
                class="row-group"
                :class="{ expanded: expandedRows.has(item.file_name) }"
              >
                <div class="table-row" @click="toggleRow(item.file_name)">
                  <div class="td col-file">
                    <span class="file-type-icon" v-html="Icons.Doc"></span>
                    <span class="text-truncate" :title="item.file_name">{{ item.file_name }}</span>
                  </div>
                  <div class="td col-id">{{ item.student_id || '-' }}</div>
                  <div class="td col-name">{{ item.student_name || '-' }}</div>
                  <div class="td col-score">
                    <div class="score-pill" :class="getScoreClass(item.display_score)">
                      <span class="status-dot" :class="getScoreClass(item.display_score) === 'score-high' ? 'ok' : getScoreClass(item.display_score) === 'score-low' ? 'err' : 'warn'"></span>
                      <span class="score-val">{{ item.display_score ?? '-' }}</span>
                      <span class="score-max" v-if="item.display_score !== null">/100</span>
                    </div>
                  </div>
                  <div class="td col-status">
                    <span class="status-dot" :class="item.status === '成功' ? 'ok' : 'err'"></span>
                    {{ item.status }}
                  </div>
                  <div class="td col-action">
                    <span class="chevron-icon" v-html="Icons.ChevronDown"></span>
                  </div>
                </div>

                <!-- Expanded Detail -->
                <div v-if="expandedRows.has(item.file_name)" class="row-detail-panel">
                  <div class="detail-card">
                    <div v-if="item.error_message" class="error-box">
                      <div class="error-title">
                        <span v-html="Icons.Alert"></span> 异常信息
                      </div>
                      <pre>{{ item.error_message }}</pre>
                    </div>

                    <div v-else class="rubric-grid">
                      <div 
                        v-for="(rItem, idx) in item.rubric_items" 
                        :key="idx"
                        class="rubric-cell"
                      >
                        <div class="cell-header">
                          <span class="cell-dim">{{ rItem.dimension }}</span>
                          <span class="cell-score">{{ rItem.score }} / {{ rItem.max_score }}</span>
                        </div>
                        <div class="cell-comment">{{ rItem.comment }}</div>
                        <div class="cell-reason" v-if="rItem.reason">
                           <span class="reason-label">理由:</span> {{ rItem.reason }}
                        </div>
                      </div>
                    </div>
                    
                    <div class="detail-footer" v-if="item.feedback">
                      <div class="feedback-title">总评</div>
                      <div class="feedback-text">{{ item.feedback }}</div>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- Empty State -->
              <div v-if="parsedFilteredItems.length === 0" class="empty-list">
                <span class="empty-text">没有找到相关记录</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </Transition>
  </div>
</template>

<style scoped>
/* --- Design System & Variables --- */
.workspace-layout {
  display: flex;
  flex-direction: column;
  gap: 32px;
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  color: var(--txt-primary);
  /* 隐形纹理背景 */
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.03'/%3E%3C/svg%3E");
  isolation: isolate;
}

/* --- Header: Command Center --- */
.workspace-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  padding: 0 8px;
}

.header-titles .page-title {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: var(--txt-primary);
  margin-bottom: 4px;
}
.header-titles .page-subtitle {
  font-size: 13px;
  color: var(--txt-tertiary);
  font-weight: 500;
  letter-spacing: 0.02em;
}

.command-bar {
  display: flex;
  align-items: center;
  gap: 24px;
  background: var(--bg-panel);
  padding: 8px 16px;
  border-radius: 16px;
  box-shadow: 
    0 4px 6px -1px rgba(0, 0, 0, 0.02),
    0 10px 15px -3px rgba(0, 0, 0, 0.04),
    0 0 0 1px rgba(0,0,0,0.04); /* 极细边界 */
  transition: transform 0.3s var(--ease-spring);
}
.command-bar:hover {
  transform: translateY(-2px);
  box-shadow: 
    0 10px 25px -5px rgba(0, 0, 0, 0.06),
    0 0 0 1px rgba(0,0,0,0.04);
}

.command-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.command-group.horizontal {
  flex-direction: row;
  align-items: center;
  gap: 12px;
}

.command-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--txt-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  user-select: none;
}
.command-label.clickable { cursor: pointer; }

/* Bento Select */
.bento-select {
  position: relative;
}
.select-trigger {
  appearance: none;
  background: var(--bg-app);
  border: 1px solid var(--border-dim);
  border-radius: 10px;
  padding: 8px 12px;
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 160px;
  justify-content: space-between;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
  color: var(--txt-secondary);
  font-size: 13px;
  font-weight: 500;
}
.select-trigger:hover {
  background: var(--bg-hover);
  border-color: var(--border-light);
  color: var(--txt-primary);
  transform: translateY(-1px);
}
.select-trigger:active {
  transform: translateY(1px);
}
.active .select-trigger {
  border-color: var(--brand);
  box-shadow: 0 0 0 2px var(--brand-dim);
}
.trigger-icon {
  width: 14px; height: 14px;
  color: var(--txt-tertiary);
}

.bento-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  width: 100%;
  min-width: 200px;
  background: var(--bg-panel);
  border: 1px solid var(--border-dim);
  border-radius: 12px;
  padding: 6px;
  box-shadow: 
    0 10px 30px -10px rgba(0,0,0,0.15),
    0 4px 6px -2px rgba(0,0,0,0.05);
  z-index: 100;
  transform-origin: top left;
}
.dropdown-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: var(--txt-secondary);
  transition: all 0.15s;
}
.dropdown-option:hover {
  background: var(--bg-hover);
  color: var(--txt-primary);
}
.dropdown-option.selected {
  background: var(--brand-dim);
  color: var(--brand);
  font-weight: 600;
}
.check-mark {
  color: var(--brand);
  width: 14px; height: 14px;
}
.backdrop-click { position: fixed; inset: 0; z-index: 90; }

.divider-vertical {
  width: 1px;
  height: 24px;
  background: var(--border-dim);
}

/* Switch */
.switch-container {
  position: relative;
  width: 36px; height: 20px;
  cursor: pointer;
}
.switch-track {
  width: 100%; height: 100%;
  background: var(--bg-active);
  border-radius: 99px;
  transition: background 0.3s;
  position: relative;
}
.switch-thumb {
  position: absolute;
  top: 2px; left: 2px;
  width: 16px; height: 16px;
  background: #fff;
  border-radius: 50%;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
input:checked ~ .switch-track { background: var(--brand); }
input:checked ~ .switch-track .switch-thumb { transform: translateX(16px); }

/* --- Upload Section --- */
.upload-section { width: 100%; }
.drop-zone-card {
  position: relative;
  width: 100%;
  height: 320px;
  border-radius: 24px;
  background: var(--bg-panel);
  border: 2px dashed var(--border-dim);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.4s cubic-bezier(0.25, 1, 0.5, 1);
  overflow: hidden;
}
.drop-zone-card:hover {
  border-color: var(--brand);
  background: linear-gradient(180deg, var(--bg-panel) 0%, var(--bg-active) 100%);
  transform: translateY(-4px);
  box-shadow: 0 20px 40px -10px rgba(0,0,0,0.08);
}
.drop-zone-card.is-dragover {
  border-color: var(--brand);
  background: var(--brand-dim);
  transform: scale(0.99);
}
.drop-zone-card.has-files {
  border-style: solid;
  border-color: var(--success);
  background: var(--bg-panel);
}

.zone-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  z-index: 10;
}

/* Visual Anchor */
.visual-anchor {
  position: relative;
  width: 80px; height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.stage-icon {
  width: 48px; height: 48px;
  color: var(--txt-tertiary);
  transition: all 0.3s;
}
.drop-zone-card:hover .stage-icon {
  color: var(--brand);
  transform: scale(1.1);
}
.stage-icon.file { color: var(--success); }

.ripple-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 1px solid var(--brand);
  opacity: 0;
  transform: scale(0.8);
}
.drop-zone-card:hover .r1 {
  animation: ripple 2s infinite cubic-bezier(0, 0, 0.2, 1);
}
.drop-zone-card:hover .r2 {
  animation: ripple 2s infinite 0.4s cubic-bezier(0, 0, 0.2, 1);
}
@keyframes ripple {
  0% { transform: scale(0.8); opacity: 0.5; border-width: 2px; }
  100% { transform: scale(2); opacity: 0; border-width: 0px; }
}

.loader-spinner {
  width: 40px; height: 40px;
  border: 3px solid var(--border-dim);
  border-top-color: var(--brand);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Text Anchor */
.text-anchor { text-align: center; }
.zone-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--txt-secondary);
  margin-bottom: 8px;
  letter-spacing: -0.01em;
}
.zone-title.highlight { color: var(--txt-primary); }
.zone-subtitle { font-size: 14px; color: var(--txt-tertiary); }
.zone-error { color: var(--error); font-size: 13px; margin-top: 8px; }

/* Action Anchor */
.bento-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 12px 32px;
  border-radius: 12px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
  border: 1px solid transparent;
}
.bento-btn.primary {
  background: var(--brand);
  color: #fff;
  box-shadow: 0 4px 12px rgba(var(--brand-rgb), 0.25);
}
.bento-btn.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(var(--brand-rgb), 0.35);
}
.bento-btn.primary:active { transform: translateY(0); box-shadow: 0 2px 8px rgba(var(--brand-rgb), 0.2); }

.bento-btn.ghost {
  background: transparent;
  color: var(--txt-tertiary);
}
.bento-btn.ghost:hover {
  color: var(--txt-primary);
  background: var(--bg-hover);
}
.btn-group { display: flex; gap: 16px; }

/* --- Results Section --- */
.results-dashboard {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* Stats Bento */
.stats-bento {
  display: grid;
  grid-template-columns: repeat(4, 1fr) 60px;
  gap: 16px;
}
.bento-card {
  background: var(--bg-panel);
  border-radius: 16px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  border: 1px solid var(--border-dim);
  transition: all 0.3s;
  position: relative;
  overflow: hidden;
}
.bento-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px -8px rgba(0,0,0,0.08);
  border-color: var(--border-light);
}
.bento-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--txt-tertiary);
  margin-bottom: 8px;
}
.bento-value {
  font-size: 32px;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: var(--txt-primary);
  line-height: 1;
}

.stat-success .bento-value { color: var(--success); }
.stat-error.has-error .bento-value { color: var(--error); }
.stat-error.has-error { border-color: rgba(239, 68, 68, 0.2); background: rgba(239, 68, 68, 0.02); }

.action-cell {
  padding: 0;
  align-items: center;
  justify-content: center;
  background: var(--bg-active);
  border: none;
}
.bento-icon-btn {
  width: 100%; height: 100%;
  border: none; background: transparent;
  color: var(--txt-secondary);
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: color 0.2s;
}
.bento-icon-btn:hover { color: var(--brand); }

/* List Module */
.list-module {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.module-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* Filter Pills */
.filter-pill-group {
  display: flex;
  gap: 4px;
  padding: 4px;
  background: var(--bg-panel);
  border-radius: 12px;
  border: 1px solid var(--border-dim);
}
.filter-pill {
  padding: 6px 16px;
  border-radius: 8px;
  border: none;
  background: transparent;
  font-size: 13px;
  font-weight: 500;
  color: var(--txt-tertiary);
  cursor: pointer;
  transition: all 0.2s;
}
.filter-pill.active {
  background: var(--bg-app);
  color: var(--txt-primary);
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.filter-pill:hover:not(.active) { color: var(--txt-secondary); }

/* Search */
.search-input-wrapper {
  display: flex;
  align-items: center;
  background: var(--bg-panel);
  border: 1px solid var(--border-dim);
  border-radius: 10px;
  padding: 8px 12px;
  width: 280px;
  transition: all 0.2s;
}
.search-input-wrapper:focus-within {
  border-color: var(--brand);
  box-shadow: 0 0 0 3px var(--brand-dim);
}
.search-icon { color: var(--txt-tertiary); margin-right: 8px; }
.clean-input {
  border: none;
  background: transparent;
  width: 100%;
  font-size: 13px;
  color: var(--txt-primary);
}
.clean-input::placeholder { color: var(--txt-tertiary); }
.clean-input:focus { outline: none; }

/* Table / List */
.module-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Header Row */
.table-header {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1fr 60px;
  padding: 0 24px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--txt-tertiary);
}

/* Rows */
.row-group {
  display: flex;
  flex-direction: column;
  transition: all 0.3s;
}
.table-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1fr 60px;
  align-items: center;
  padding: 16px 24px;
  background: var(--bg-panel);
  border: 1px solid var(--border-dim);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
  position: relative;
  z-index: 1;
}
.table-row:hover {
  transform: translateY(-2px) scale(1.005);
  box-shadow: 0 8px 20px -6px rgba(0,0,0,0.06);
  border-color: var(--border-light);
  z-index: 10;
}
.row-group.expanded .table-row {
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
  border-bottom-color: transparent;
  background: var(--bg-active);
  transform: none;
  box-shadow: none;
}

/* Cells */
.td { font-size: 13px; color: var(--txt-secondary); display: flex; align-items: center; }
.col-file { color: var(--txt-primary); font-weight: 500; gap: 12px; }
.file-type-icon { color: var(--brand); opacity: 0.8; }
.text-truncate { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 90%; }

.col-score { 
  font-family: 'JetBrains Mono', monospace; 
  font-weight: 600; 
  justify-content: flex-end;
  padding-right: 24px;
}
.score-pill { 
  display: inline-flex; 
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  border-radius: 99px;
  background: var(--bg-app);
  border: 1px solid var(--border-dim);
  min-width: 64px;
  justify-content: center;
}
.score-pill.high { border-color: var(--success); color: var(--success); background: var(--success-bg); }
.score-pill.mid { border-color: var(--warning); color: var(--warning); background: var(--warning-bg); }
.score-pill.low { border-color: var(--error); color: var(--error); background: var(--error-bg); }

.score-val { font-size: 14px; }
.score-max { font-size: 11px; opacity: 0.6; margin-left: 2px; }

.status-dot { width: 6px; height: 6px; border-radius: 50%; margin-right: 8px; }
.status-dot.ok { background: var(--success); box-shadow: 0 0 6px var(--success-bg); }
.status-dot.err { background: var(--error); box-shadow: 0 0 6px var(--error-bg); }

.col-action { justify-content: center; }
.chevron-icon { color: var(--txt-tertiary); transition: transform 0.3s; }
.row-group.expanded .chevron-icon { transform: rotate(180deg); }

/* Detail Panel */
.row-detail-panel {
  background: var(--bg-active);
  border: 1px solid var(--border-dim);
  border-top: none;
  border-bottom-left-radius: 12px;
  border-bottom-right-radius: 12px;
  padding: 0 24px 24px 24px;
  margin-top: -1px;
  animation: slideDown 0.3s var(--ease-out);
}
@keyframes slideDown {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

.detail-card {
  background: var(--bg-app);
  border-radius: 8px;
  padding: 24px;
  border: 1px dashed var(--border-dim);
}

.error-box {
  color: var(--error);
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.error-title { display: flex; align-items: center; gap: 8px; font-weight: 600; }

.rubric-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
.rubric-cell {
  background: var(--bg-panel);
  padding: 16px;
  border-radius: 8px;
  border: 1px solid var(--border-dim);
}
.cell-header {
  display: flex; justify-content: space-between; margin-bottom: 8px;
}
.cell-dim { font-size: 11px; font-weight: 600; color: var(--txt-secondary); }
.cell-score { font-family: 'JetBrains Mono'; font-weight: 700; font-size: 13px; color: var(--brand); }
.cell-comment { font-size: 13px; color: var(--txt-primary); line-height: 1.5; margin-bottom: 8px; }
.cell-reason { font-size: 12px; color: var(--txt-tertiary); background: var(--bg-app); padding: 8px; border-radius: 6px; }

.detail-footer { margin-top: 24px; padding-top: 16px; border-top: 1px solid var(--border-dim); }
.feedback-title { font-size: 11px; font-weight: 600; color: var(--txt-tertiary); margin-bottom: 8px; text-transform: uppercase; }
.feedback-text { font-size: 14px; line-height: 1.6; color: var(--txt-primary); }

/* Empty State */
.empty-list {
  text-align: center;
  padding: 48px;
  color: var(--txt-tertiary);
  font-size: 14px;
}

@media (max-width: 900px) {
  .stats-bento { grid-template-columns: 1fr 1fr; }
  .table-row, .table-header { grid-template-columns: 1fr 80px 40px; }
  .col-id, .col-name, .col-action { display: none; }
}
</style>
