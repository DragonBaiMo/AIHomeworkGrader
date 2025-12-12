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

const Icons = {
  Upload: `<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>`,
  Doc: `<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>`,
  Check: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`,
  Download: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>`,
  Alert: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`,
  ChevronDown: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>`,
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
    hint.value = "仅支持 .docx / .md / .txt";
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
    <!-- Header -->
    <header class="workspace-header">
      <div class="header-content">
        <h1 class="page-title">智能批改台</h1>
        <p class="page-subtitle">AI 驱动的自动化评估系统</p>
      </div>

      <div class="control-island glass">
        <div class="island-group">
          <label class="island-label">评估模板</label>
          <div class="select-wrapper">
            <select 
              class="island-select"
              :value="config.template"
              @change="updateConfigField('template', ($event.target as HTMLSelectElement).value)"
            >
              <option v-for="t in templates" :key="t.value" :value="t.value">{{ t.label }}</option>
            </select>
            <span class="select-icon" v-html="Icons.ChevronDown"></span>
          </div>
        </div>
        
        <div class="island-divider"></div>
        
        <div class="island-group row">
          <label class="toggle-switch">
            <input 
              type="checkbox" 
              :checked="config.mock"
              @change="updateConfigField('mock', ($event.target as HTMLInputElement).checked)"
            />
            <span class="toggle-track"></span>
          </label>
          <span class="island-label clickable">模拟模式</span>
        </div>
      </div>
    </header>

    <!-- Drop Zone -->
    <section class="upload-section">
      <div
        class="energy-field"
        :class="{ 
          'is-active': dragOver, 
          'has-content': files.length > 0,
          'is-processing': loading 
        }"
        @dragover.prevent="dragOver = true"
        @dragleave="dragOver = false"
        @drop="onDrop"
      >
        <div class="field-content">
          <div class="core-visual">
            <div class="ripple r1"></div>
            <div class="ripple r2"></div>
            <div class="icon-container" v-if="loading">
              <div class="loader-ring"></div>
            </div>
            <div class="icon-container" v-else-if="files.length" v-html="Icons.Doc"></div>
            <div class="icon-container" v-else v-html="Icons.Upload"></div>
          </div>

          <div class="field-text">
            <h3 v-if="loading" class="status-heading">正在深度分析...</h3>
            <h3 v-else-if="files.length" class="status-heading file-loaded">{{ fileSummary }}</h3>
            <h3 v-else class="status-heading">拖入作业文档</h3>
            
            <p v-if="!loading" class="status-sub">支持 Word (.docx) 或 Markdown (.md)</p>
            <p v-if="hint" class="status-hint">{{ hint }}</p>
          </div>

          <div class="field-actions" v-if="!loading">
            <label v-if="!files.length" class="btn primary glow">
              选择文件
              <input type="file" accept=".docx,.md,.markdown,.txt" multiple hidden @change="onFileChange" />
            </label>
            
            <div v-else class="action-row">
              <button class="btn ghost" @click="files = []">清空</button>
              <button class="btn primary glow" @click="handleSubmit">开始批改</button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Results Area -->
    <Transition name="slide-up">
      <section v-if="result" class="results-section">
        
        <div class="dashboard-grid">
          <div class="stat-card glass">
            <span class="stat-label">总文件</span>
            <span class="stat-value">{{ result.total_files }}</span>
          </div>
          <div class="stat-card glass success">
            <span class="stat-label">成功</span>
            <span class="stat-value">{{ result.success_count }}</span>
          </div>
          <div class="stat-card glass" :class="{ error: result.error_count > 0 }">
            <span class="stat-label">异常</span>
            <span class="stat-value">{{ result.error_count }}</span>
          </div>
          <div class="stat-card glass highlight">
            <span class="stat-label">平均分</span>
            <span class="stat-value">{{ result.average_score ?? "-" }}</span>
          </div>
          
          <div class="stat-actions glass">
            <a :href="result.download_result_url" class="btn primary small icon-btn">
              <span v-html="Icons.Download"></span> 报告
            </a>
            <a v-if="result.error_count > 0" :href="result.download_error_url" class="btn danger small icon-btn">
              <span v-html="Icons.Alert"></span> 异常
            </a>
          </div>
        </div>

        <div class="list-container glass">
          <div class="list-toolbar">
            <div class="filter-tabs">
              <button class="tab-btn" :class="{ active: resultFilter === 'all' }" @click="resultFilter = 'all'">全部</button>
              <button class="tab-btn" :class="{ active: resultFilter === 'success' }" @click="resultFilter = 'success'">成功</button>
              <button class="tab-btn" :class="{ active: resultFilter === 'fail' }" @click="resultFilter = 'fail'">失败</button>
            </div>
            
            <div class="search-box">
              <span class="search-icon" v-html="Icons.Search"></span>
              <input type="text" v-model="resultQuery" placeholder="搜索姓名或学号..." />
            </div>
          </div>

          <div class="list-grid">
            <div class="grid-row header">
              <div class="col file">文件名称</div>
              <div class="col id">学号</div>
              <div class="col name">姓名</div>
              <div class="col score">得分</div>
              <div class="col rubric">细则分</div>
              <div class="col status">状态</div>
            </div>

            <div 
              v-for="item in filteredItems" 
              :key="item.file_name"
              class="grid-group"
              :class="{ expanded: expandedRows.has(item.file_name) }"
            >
              <div class="grid-row item" @click="toggleRow(item.file_name)">
                <div class="col file" :title="item.file_name">
                  <span class="file-icon" v-html="Icons.Doc"></span>
                  {{ item.file_name }}
                </div>
                <div class="col id mono">{{ item.student_id || "-" }}</div>
                <div class="col name">{{ item.student_name || "-" }}</div>
                <div class="col score mono font-bold">
                  {{ item.score ?? "-" }}
                </div>
                <div class="col rubric mono muted">
                  {{ item.score_rubric ?? "-" }} / {{ item.score_rubric_max ?? "-" }}
                </div>
                <div class="col status">
                  <span class="status-pill" :class="item.status === '成功' ? 'ok' : 'err'">
                    {{ item.status }}
                  </span>
                </div>
              </div>

              <div class="row-detail" v-if="expandedRows.has(item.file_name)">
                <div class="detail-inner">
                  <div class="detail-block">
                    <span class="detail-label">AI 评语</span>
                    <p class="detail-content">{{ item.comment || "无评语" }}</p>
                  </div>
                  <div class="detail-block" v-if="item.error_message">
                    <span class="detail-label error">错误信息</span>
                    <pre class="detail-content error">{{ item.error_message }}</pre>
                  </div>
                  <div class="detail-block">
                    <span class="detail-label">JSON 明细</span>
                    <pre class="detail-content code">{{ item.detail_json }}</pre>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="filteredItems.length === 0" class="empty-state">
              没有找到相关记录
            </div>
          </div>
        </div>
      </section>
    </Transition>
  </div>
</template>

<style scoped>
/* --- Layout --- */
.workspace-layout {
  display: flex;
  flex-direction: column;
  gap: 32px;
  max-width: 1000px;
  margin: 0 auto;
  padding-bottom: 60px;
}

/* --- Header --- */
.workspace-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  flex-wrap: wrap;
  gap: 24px;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--txt-primary);
  margin-bottom: 4px;
}
.page-subtitle {
  font-size: 14px;
  color: var(--txt-tertiary);
}

/* --- Control Island --- */
.control-island {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  border-radius: 99px; /* Pill Shape */
  gap: 20px;
  box-shadow: var(--shadow-card);
  height: 52px;
}

.island-group {
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.island-group.row {
  flex-direction: row;
  align-items: center;
  gap: 10px;
}

.island-label {
  font-size: 10px;
  color: var(--txt-tertiary);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 2px;
}
.island-label.clickable { margin-bottom: 0; cursor: pointer; }

/* Select Hack */
.select-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}
.island-select {
  appearance: none;
  background: transparent;
  border: none;
  color: var(--txt-primary);
  font-size: 14px;
  font-weight: 600;
  padding-right: 20px;
  cursor: pointer;
}
.select-icon {
  position: absolute;
  right: 0;
  color: var(--txt-tertiary);
  pointer-events: none;
  display: flex;
}

.island-divider {
  width: 1px;
  height: 24px;
  background: var(--border-light);
}

/* Toggle Switch */
.toggle-switch {
  position: relative;
  width: 36px;
  height: 20px;
  cursor: pointer;
}
.toggle-switch input { display: none; }
.toggle-track {
  position: absolute; inset: 0;
  background: var(--bg-active);
  border-radius: 99px;
  transition: all 0.3s var(--ease-spring);
  border: 1px solid var(--border-dim);
}
.toggle-track::after {
  content: '';
  position: absolute;
  top: 2px; left: 2px;
  width: 14px; height: 14px;
  background: var(--txt-secondary);
  border-radius: 50%;
  transition: all 0.3s var(--ease-spring);
  box-shadow: 0 1px 2px rgba(0,0,0,0.2);
}
input:checked + .toggle-track {
  background: var(--brand);
  border-color: var(--brand);
}
input:checked + .toggle-track::after {
  transform: translateX(16px);
  background: #fff;
}

/* --- Upload Section (Energy Field) --- */
.upload-section {
  width: 100%;
}
.energy-field {
  position: relative;
  width: 100%;
  min-height: 360px;
  border-radius: var(--radius-xl);
  background: radial-gradient(circle at center, var(--bg-panel) 0%, var(--bg-card) 100%);
  border: 1px dashed var(--border-light);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.5s var(--ease-spring);
  overflow: hidden;
}

.energy-field:hover, .energy-field.is-active {
  border-color: var(--brand);
  border-style: solid;
  box-shadow: 0 0 30px -10px var(--brand-dim);
  transform: translateY(-4px);
}
.energy-field.has-content {
  border-style: solid;
  border-color: var(--success);
  background: radial-gradient(circle at center, var(--success-bg) 0%, var(--bg-card) 100%);
}

.field-content {
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  text-align: center;
}

/* Visual Core */
.core-visual {
  position: relative;
  width: 100px;
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.icon-container {
  color: var(--txt-tertiary);
  transition: color 0.3s;
  z-index: 2;
}
.energy-field:hover .icon-container { color: var(--brand); }
.energy-field.has-content .icon-container { color: var(--success); }

/* Ripples */
.ripple {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 1px solid var(--border-light);
  opacity: 0;
  transform: scale(0.8);
  transition: all 0.6s var(--ease-out);
}
.energy-field:hover .ripple {
  opacity: 1;
  border-color: var(--brand-dim);
}
.energy-field:hover .r1 { transform: scale(1.4); opacity: 0.5; }
.energy-field:hover .r2 { transform: scale(1.8); opacity: 0.2; transition-delay: 0.1s; }

/* Text */
.status-heading {
  font-size: 20px;
  font-weight: 600;
  color: var(--txt-secondary);
}
.status-heading.file-loaded { color: var(--txt-primary); }
.status-sub { font-size: 14px; color: var(--txt-tertiary); }
.status-hint { font-size: 13px; color: var(--error); margin-top: 8px; }

/* Actions */
.field-actions { margin-top: 8px; }
.action-row { display: flex; gap: 12px; }
.glow:hover { box-shadow: 0 0 20px var(--brand-glow); }

/* Loader */
.loader-ring {
  width: 48px; height: 48px;
  border: 3px solid var(--bg-active);
  border-top-color: var(--brand);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* --- Results Section --- */
.results-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* Dashboard Grid */
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr) auto;
  gap: 16px;
}
.stat-card {
  display: flex;
  flex-direction: column;
  padding: 16px 20px;
  border-radius: var(--radius-m);
  min-height: 88px;
  justify-content: center;
}
.stat-label { font-size: 11px; color: var(--txt-tertiary); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
.stat-value { font-size: 28px; font-weight: 700; color: var(--txt-primary); line-height: 1; letter-spacing: -0.02em; }
.stat-card.success .stat-value { color: var(--success); }
.stat-card.error .stat-value { color: var(--error); }
.stat-card.highlight .stat-value { color: var(--brand); }

.stat-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  border-radius: var(--radius-m);
  justify-content: center;
}
.icon-btn { justify-content: flex-start; }

/* List Container */
.list-container {
  border-radius: var(--radius-l);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 400px;
}

.list-toolbar {
  padding: 16px 24px;
  border-bottom: 1px solid var(--border-dim);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-tabs {
  display: flex;
  background: var(--bg-active);
  padding: 4px;
  border-radius: 8px;
}
.tab-btn {
  border: none; background: transparent;
  color: var(--txt-tertiary);
  padding: 6px 12px;
  font-size: 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}
.tab-btn.active { background: var(--bg-panel); color: var(--txt-primary); shadow: 0 1px 2px rgba(0,0,0,0.1); }

.search-box {
  display: flex;
  align-items: center;
  background: var(--bg-active);
  border-radius: 8px;
  padding: 0 12px;
  width: 240px;
  border: 1px solid transparent;
}
.search-box:focus-within { border-color: var(--brand); }
.search-icon { color: var(--txt-tertiary); margin-right: 8px; display: flex; }
.search-box input {
  border: none; background: transparent; padding: 8px 0;
  font-size: 13px; width: 100%; box-shadow: none;
}

/* Grid Table */
.list-grid { display: flex; flex-direction: column; }

.grid-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 0.8fr 1fr 1fr;
  align-items: center;
  padding: 14px 24px;
  gap: 16px;
  border-bottom: 1px solid var(--border-dim);
}
.grid-row.header {
  background: var(--bg-active);
  font-size: 11px;
  font-weight: 600;
  color: var(--txt-tertiary);
  letter-spacing: 0.05em;
  text-transform: uppercase;
  border-bottom: none;
}

.grid-group { transition: background 0.2s; }
.grid-group:hover { background: var(--bg-hover); }
.grid-group.expanded { background: var(--bg-hover); box-shadow: inset 3px 0 0 var(--brand); }

.grid-row.item { cursor: pointer; }

.col { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 13px; color: var(--txt-secondary); }
.col.file { color: var(--txt-primary); display: flex; align-items: center; gap: 8px; font-weight: 500; }
.file-icon { color: var(--txt-tertiary); }
.col.status { display: flex; }

.status-pill {
  font-size: 11px; padding: 2px 8px; border-radius: 4px;
  font-weight: 600;
}
.status-pill.ok { background: var(--success-bg); color: var(--success); }
.status-pill.err { background: var(--error-bg); color: var(--error); }

.row-detail {
  padding: 0 24px 24px 24px;
  animation: slideDown 0.3s var(--ease-out);
}
.detail-inner {
  background: var(--bg-app);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--border-dim);
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.detail-block { display: flex; flex-direction: column; gap: 6px; }
.detail-label { font-size: 11px; color: var(--txt-tertiary); font-weight: 600; }
.detail-content { font-size: 13px; line-height: 1.6; color: var(--txt-secondary); white-space: pre-wrap; font-family: "JetBrains Mono"; }
.detail-content.error { color: var(--error); }

.empty-state { padding: 40px; text-align: center; color: var(--txt-tertiary); }

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 800px) {
  .dashboard-grid { grid-template-columns: 1fr 1fr; }
  .stat-card:last-child { grid-column: span 2; }
  .grid-row { grid-template-columns: 1fr auto; gap: 8px; }
  .col:not(.file):not(.status) { display: none; }
}
</style>