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

// --- Icons ---
const Icons = {
  Upload: `<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>`,
  Doc: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>`,
  CheckCircle: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>`,
  Download: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>`,
  Alert: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`
};

const fileSummary = computed(() => {
  if (!files.value.length) return "";
  const total = files.value.length;
  const sizeMB = files.value.reduce((acc, cur) => acc + cur.size, 0) / 1024 / 1024;
  return `${total} 个文件 · ${sizeMB.toFixed(2)} MB`;
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

function isRowExpanded(key: string) {
  return expandedRows.value.has(key);
}

const SUPPORTED_EXTENSIONS = [".docx", ".md", ".markdown", ".txt"] as const;

function isSupportedFileName(fileName: string): boolean {
  const lower = fileName.toLowerCase();
  return SUPPORTED_EXTENSIONS.some((ext) => lower.endsWith(ext));
}

function updateFiles(list: FileList | File[]) {
  files.value = Array.from(list).filter((file) => isSupportedFileName(file.name));
  if (!files.value.length) {
    hint.value = "系统仅接受 .docx/.md/.markdown/.txt 格式文件";
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
  if (!files.value.length) {
    hint.value = "请先上传文件";
    return;
  }
  if (!props.config.mock && !props.config.apiUrl) {
    emit("request-settings");
    return;
  }
  hint.value = "";
  emit("submit", files.value);
}

function updateConfigField<T extends keyof GradeConfigPayload>(key: T, value: GradeConfigPayload[T]) {
  emit("update:config", { [key]: value } as Partial<GradeConfigPayload>);
}
</script>

<template>
  <div class="workspace-stage">
    <!-- Header Area -->
    <header class="stage-header">
      <div class="header-titles">
        <h2 class="title">智能批改台</h2>
        <p class="subtitle">AI 驱动的自动化作业评估与归档系统</p>
      </div>

      <!-- Control Pill -->
      <div class="control-pill glass">
        <div class="pill-group">
          <label class="pill-label">评估模板</label>
          <div class="pill-select-wrap">
            <select 
              class="pill-select"
              :value="config.template"
              @change="updateConfigField('template', ($event.target as HTMLSelectElement).value)"
            >
              <option v-for="t in templates" :key="t.value" :value="t.value">{{ t.label }}</option>
            </select>
            <span class="pill-chevron" aria-hidden="true">▾</span>
          </div>
        </div>
        
        <div class="pill-divider mobile-hide"></div>
        
        <div class="pill-group toggle-group mobile-hide">
          <label class="pill-toggle">
            <input 
              type="checkbox" 
              :checked="config.mock"
              @change="updateConfigField('mock', ($event.target as HTMLInputElement).checked)"
            />
            <span class="toggle-track"></span>
            <span class="toggle-text">模拟</span>
          </label>
        </div>
      </div>
    </header>

    <!-- Main Drop Zone -->
    <div
      class="drop-zone card"
      :class="{ 
        'is-dragover': dragOver, 
        'has-files': files.length > 0, 
        'is-loading': loading 
      }"
      @dragover.prevent="dragOver = true"
      @dragleave="dragOver = false"
      @drop="onDrop"
    >
      <div class="zone-content animate-in">
        <!-- Visual -->
        <div class="visual-anchor">
          <div class="ripple-ring"></div>
          <div class="icon-box" v-if="files.length" v-html="Icons.Doc"></div>
          <div class="icon-box" v-else v-html="Icons.Upload"></div>
        </div>

        <!-- Text -->
        <div class="feedback-text">
          <h3 v-if="loading" class="status-text">AI 正在深度分析...</h3>
          <h3 v-else-if="files.length" class="file-info">{{ fileSummary }}</h3>
          <h3 v-else class="prompt-text">拖拽作业文件（.docx/.md/.markdown/.txt）</h3>
          
          <p v-if="!loading && !files.length" class="sub-prompt">点击此处或将文件拖入</p>
        </div>

        <!-- Actions -->
        <div class="action-dock" v-if="!loading">
          <label v-if="!files.length" class="btn primary glow-effect">
            选择文件
            <input type="file" accept=".docx,.md,.markdown,.txt" multiple hidden @change="onFileChange" />
          </label>
          
          <div v-else class="dock-buttons">
            <button class="btn ghost" @click="files = []">清空</button>
            <button class="btn primary glow-effect" @click="handleSubmit">开始批改</button>
          </div>
        </div>
      </div>

      <!-- Loader -->
      <div v-if="loading" class="loader-overlay">
        <div class="spinner"></div>
      </div>
    </div>

    <!-- Result Dashboard -->
    <Transition name="slide-up">
      <div v-if="result" class="result-dashboard card">
        <div class="dashboard-header">
          <div class="batch-meta">
            <span class="meta-label">批次 ID</span>
            <span class="meta-val">{{ result.batch_id.slice(-8).toUpperCase() }}</span>
          </div>
          <div class="status-tag success">
            <span class="icon" v-html="Icons.CheckCircle"></span>
            批改完成
          </div>
        </div>

        <div class="metrics-grid">
          <div class="metric-card">
            <span class="label">文件总数</span>
            <span class="value">{{ result.total_files }}</span>
          </div>
          <div class="metric-card">
            <span class="label">成功处理</span>
            <span class="value success-text">{{ result.success_count }}</span>
          </div>
          <div class="metric-card">
            <span class="label">异常数量</span>
            <span class="value" :class="{ 'error-text': result.error_count > 0 }">{{ result.error_count }}</span>
          </div>
          <div class="metric-card highlight">
            <span class="label">平均分数</span>
            <span class="value brand-text">{{ result.average_score ?? "-" }}</span>
          </div>
        </div>

        <div class="dashboard-footer">
          <div class="download-group">
            <a :href="result.download_result_url" class="btn primary full-width-mobile">
              <span v-html="Icons.Download"></span> 下载报告
            </a>
            <a v-if="result.error_count > 0" :href="result.download_error_url" class="btn danger full-width-mobile">
              <span v-html="Icons.Alert"></span> 下载异常
            </a>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Result List -->
    <Transition name="slide-up">
      <div v-if="result" class="result-list card">
        <div class="list-head">
          <div class="list-title">批改结果明细</div>
          <div class="list-actions">
            <div class="seg">
              <button class="seg-btn" :class="{ active: resultFilter === 'all' }" @click="resultFilter = 'all'">全部</button>
              <button class="seg-btn" :class="{ active: resultFilter === 'success' }" @click="resultFilter = 'success'">成功</button>
              <button class="seg-btn" :class="{ active: resultFilter === 'fail' }" @click="resultFilter = 'fail'">失败</button>
            </div>
            <input class="search" type="text" v-model="resultQuery" placeholder="搜索：文件名 / 学号 / 姓名" />
          </div>
        </div>

        <div class="table">
          <div class="row head">
            <div class="cell file">文件</div>
            <div class="cell id">学号</div>
            <div class="cell name">姓名</div>
            <div class="cell score">最终分</div>
            <div class="cell rubric">规则分</div>
            <div class="cell status">状态</div>
            <div class="cell more">明细</div>
          </div>

          <div v-for="item in filteredItems" :key="item.file_name" class="row">
            <div class="cell file mono" :title="item.file_name">{{ item.file_name }}</div>
            <div class="cell id mono">{{ item.student_id || "-" }}</div>
            <div class="cell name">{{ item.student_name || "-" }}</div>
            <div class="cell score mono">
              <span v-if="item.score !== null">{{ item.score }}</span>
              <span v-else class="muted">-</span>
            </div>
            <div class="cell rubric mono">
              <span v-if="item.score_rubric !== null && item.score_rubric_max !== null">{{ item.score_rubric }} / {{ item.score_rubric_max }}</span>
              <span v-else class="muted">-</span>
            </div>
            <div class="cell status">
              <span class="badge" :class="{ ok: item.status === '成功', bad: item.status !== '成功' }">{{ item.status }}</span>
            </div>
            <div class="cell more">
              <button class="link" @click="toggleRow(item.file_name)">{{ isRowExpanded(item.file_name) ? "收起" : "展开" }}</button>
            </div>

            <div v-if="isRowExpanded(item.file_name)" class="detail">
              <div v-if="item.status !== '成功'" class="detail-error">
                <div class="detail-title">失败原因</div>
                <pre class="detail-text selectable">{{ item.error_message || "未提供错误信息。" }}</pre>
              </div>
              <div v-else class="detail-ok">
                <div class="detail-title">总体评语</div>
                <pre class="detail-text selectable">{{ item.comment || "未提供评语。" }}</pre>
                <div class="detail-title">评分明细（原始 JSON）</div>
                <pre class="detail-text selectable">{{ item.detail_json || "未提供评分明细。" }}</pre>
              </div>
            </div>
          </div>

          <div v-if="!filteredItems.length" class="empty">没有匹配的结果。</div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.workspace-stage {
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 40px;
}

@media (max-width: 768px) {
  .workspace-stage { gap: 24px; padding-bottom: 80px; /* Space for bottom nav */ }
}

/* --- Header & Control Pill --- */
.stage-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  flex-wrap: wrap;
  gap: 16px;
}
.title { font-size: 28px; font-weight: 700; color: var(--txt-primary); margin-bottom: 4px; }
.subtitle { font-size: 14px; color: var(--txt-tertiary); }

@media (max-width: 600px) {
  .title { font-size: 24px; }
  .stage-header { flex-direction: column; align-items: flex-start; }
  .control-pill { width: 100%; justify-content: space-between; }
}

.control-pill {
  display: flex;
  align-items: center;
  padding: 10px 14px;
  border-radius: var(--radius-l);
  gap: 18px;
  min-height: 56px;
  box-shadow: var(--shadow-card);
}
@media (max-width: 600px) {
  .control-pill { border-radius: 12px; height: auto; padding: 12px; }
  .mobile-hide { display: none; }
}


.pill-group {
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.pill-label {
  font-size: 11px;
  color: var(--txt-tertiary);
  font-weight: 600;
  letter-spacing: 0.05em;
  margin-bottom: 2px;
}
.pill-select-wrap {
  position: relative;
  display: flex;
  align-items: center;
  background: var(--bg-hover);
  border: 1px solid var(--border-dim);
  border-radius: var(--radius-m);
  padding: 8px 34px 8px 12px;
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.2s;
}
.pill-select-wrap:focus-within {
  border-color: var(--brand);
  box-shadow: 0 0 0 3px var(--brand-dim);
  transform: translateY(-1px);
}
.pill-chevron {
  position: absolute;
  right: 12px;
  color: var(--txt-tertiary);
  font-size: 12px;
  pointer-events: none;
}
.pill-select {
  appearance: none;
  background: transparent;
  border: none;
  color: var(--txt-primary);
  font-size: 14px;
  padding: 0;
  font-weight: 600;
  cursor: pointer;
  width: 200px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
@media (max-width: 600px) {
  .pill-select { width: 100%; }
}

.pill-divider {
  width: 1px;
  height: 24px;
  background: var(--border-light);
}

/* Toggle Switch */
.pill-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.pill-toggle input { display: none; }
.toggle-track {
  width: 32px;
  height: 18px;
  background: var(--bg-active);
  border-radius: 99px;
  position: relative;
  transition: all 0.3s;
  border: 1px solid var(--border-light);
}
.toggle-track::after {
  content: '';
  position: absolute;
  left: 2px; top: 2px;
  width: 12px; height: 12px;
  background: var(--txt-secondary);
  border-radius: 50%;
  transition: all 0.3s var(--ease-spring);
}
.pill-toggle input:checked + .toggle-track { background: var(--brand-dim); border-color: var(--brand); }
.pill-toggle input:checked + .toggle-track::after { transform: translateX(14px); background: var(--brand); }
.toggle-text { font-size: 12px; font-weight: 600; color: var(--txt-secondary); }
.pill-toggle input:checked ~ .toggle-text { color: var(--txt-primary); }

/* --- Drop Zone --- */
.drop-zone {
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-style: dashed;
  border-width: 1px;
  border-color: var(--border-light);
  background: radial-gradient(circle at center, var(--bg-panel) 0%, var(--bg-card) 100%);
  transition: all 0.4s var(--ease-spring);
}
@media (max-width: 600px) {
  .drop-zone { min-height: 280px; border-width: 2px; }
}

.drop-zone:hover, .drop-zone.is-dragover {
  border-color: var(--brand);
  border-style: solid;
  transform: translateY(-4px);
  box-shadow: var(--shadow-float), 0 0 30px var(--brand-dim);
}

.drop-zone.has-files {
  border-style: solid;
  border-color: var(--success);
  background: radial-gradient(circle at center, rgba(16,185,129,0.05) 0%, var(--bg-card) 100%);
}

.zone-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;
  z-index: 10;
  text-align: center;
  padding: 20px;
}

/* Visual Anchor */
.visual-anchor {
  position: relative;
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.icon-box {
  color: var(--txt-secondary);
  transition: color 0.3s;
}
.drop-zone:hover .icon-box { color: var(--brand); }
.drop-zone.has-files .icon-box { color: var(--success); }

.ripple-ring {
  position: absolute;
  inset: -20px;
  border-radius: 50%;
  border: 1px solid var(--border-light);
  opacity: 0;
  transform: scale(0.8);
  transition: all 0.5s var(--ease-out);
}
.drop-zone:hover .ripple-ring {
  opacity: 1;
  transform: scale(1);
  border-color: var(--brand-dim);
}

/* Typography */
.status-text { font-size: 18px; color: var(--brand); font-weight: 500; animation: pulseText 2s infinite; }
.file-info { font-size: 20px; color: var(--txt-primary); font-weight: 600; }
.prompt-text { font-size: 18px; color: var(--txt-secondary); font-weight: 500; }
.sub-prompt { font-size: 14px; color: var(--txt-tertiary); }

/* Buttons */
.dock-buttons { display: flex; gap: 16px; flex-wrap: wrap; justify-content: center; }
.glow-effect:hover { box-shadow: 0 0 20px var(--brand-glow); }

/* Loader */
.loader-overlay {
  position: absolute;
  inset: 0;
  background: rgba(9, 9, 11, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 20;
}
.spinner {
  width: 48px; height: 48px;
  border: 3px solid var(--border-light);
  border-top-color: var(--brand);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

/* Toast */
.toast-message {
  position: absolute;
  bottom: 24px;
  background: var(--error-bg);
  color: #fca5a5;
  border: 1px solid rgba(239, 68, 68, 0.2);
  padding: 8px 16px;
  border-radius: 99px;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 8px;
  width: calc(100% - 40px);
  justify-content: center;
  left: 50%;
  transform: translateX(-50%);
}

/* --- Result Dashboard --- */
.result-dashboard {
  padding: 0; /* Layout handled by grid */
  background: var(--bg-card);
}
.dashboard-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-dim);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.meta-label { font-size: 10px; color: var(--txt-tertiary); letter-spacing: 0.1em; display: block; }
.meta-val { font-family: "JetBrains Mono", monospace; font-size: 14px; color: var(--txt-primary); }

.status-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 99px;
  background: var(--success-bg);
  color: var(--success);
}
.status-tag .icon svg { width: 14px; height: 14px; }

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  padding: 32px 24px;
  gap: 24px;
}

@media (max-width: 600px) {
  .metrics-grid { grid-template-columns: repeat(2, 1fr); gap: 20px; padding: 20px; }
  .metric-card { border-right: none !important; }
  .metric-card:nth-child(odd) { border-right: 1px solid var(--border-dim) !important; padding-right: 12px; }
  .metric-card:nth-child(even) { padding-left: 12px; }
}

.metric-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-right: 24px;
  border-right: 1px solid var(--border-dim);
}
.metric-card:last-child { border-right: none; }

.metric-card .label { font-size: 11px; color: var(--txt-tertiary); text-transform: uppercase; letter-spacing: 0.05em; }
.metric-card .value { font-size: 32px; font-weight: 600; line-height: 1; color: var(--txt-primary); letter-spacing: -0.03em; }
@media (max-width: 600px) { .metric-card .value { font-size: 24px; } }

.metric-card .value.brand-text { color: var(--brand); }
.metric-card .value.success-text { color: var(--success); }
.metric-card .value.error-text { color: var(--error); }

.dashboard-footer {
  padding: 20px 24px;
  background: var(--bg-panel);
  border-top: 1px solid var(--border-dim);
  display: flex;
  justify-content: flex-end;
}
@media (max-width: 600px) { .dashboard-footer { flex-direction: column; } }

.download-group { display: flex; gap: 12px; }
@media (max-width: 600px) { .download-group { flex-direction: column; width: 100%; } }

.full-width-mobile { width: 100%; justify-content: center; }

/* --- Result List --- */
.result-list { padding: 0; background: var(--bg-card); overflow: hidden; }
.list-head {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-dim);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
.list-title { font-size: 14px; font-weight: 700; color: var(--txt-primary); }
.list-actions { display: flex; align-items: center; gap: 12px; }
.search {
  width: 240px;
  background: var(--bg-app);
  border: 1px solid var(--border-dim);
  border-radius: 10px;
  padding: 8px 10px;
  color: var(--txt-primary);
  font-size: 12px;
}
.seg { display: inline-flex; border: 1px solid var(--border-dim); border-radius: 10px; overflow: hidden; }
.seg-btn {
  background: transparent;
  border: none;
  padding: 8px 10px;
  font-size: 12px;
  color: var(--txt-tertiary);
  cursor: pointer;
}
.seg-btn.active { background: var(--bg-active); color: var(--txt-primary); }

.table { width: 100%; }
.row {
  display: grid;
  grid-template-columns: 2.2fr 1fr 1fr 0.8fr 1.1fr 0.7fr 0.6fr;
  gap: 0;
  align-items: center;
  padding: 10px 20px;
  border-bottom: 1px solid var(--border-dim);
}
.row.head { background: var(--bg-panel); color: var(--txt-tertiary); font-size: 11px; font-weight: 600; }
.cell { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.cell.mono, .mono { font-family: "JetBrains Mono", monospace; }
.muted { color: var(--txt-tertiary); }
.badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 12px;
  border: 1px solid var(--border-dim);
}
.badge.ok { background: var(--success-bg); color: var(--success); border-color: rgba(16,185,129,0.25); }
.badge.bad { background: var(--error-bg); color: var(--error); border-color: rgba(239,68,68,0.25); }
.link {
  background: transparent;
  border: none;
  color: var(--brand);
  cursor: pointer;
  padding: 0;
  font-size: 12px;
}
.detail {
  grid-column: 1 / -1;
  margin-top: 10px;
  padding: 12px;
  border: 1px solid var(--border-dim);
  border-radius: 12px;
  background: var(--bg-app);
}
.detail-title { font-size: 12px; color: var(--txt-tertiary); margin-bottom: 6px; }
.detail-text {
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 12px;
  line-height: 1.6;
  color: var(--txt-secondary);
  margin: 0 0 10px 0;
  font-family: "JetBrains Mono", monospace;
}
.detail-text.selectable { user-select: text; }
.empty { padding: 16px 20px; color: var(--txt-tertiary); font-size: 12px; }

/* Animations */
@keyframes spin { to { transform: rotate(360deg); } }
@keyframes pulseText { 50% { opacity: 0.6; } }

.slide-up-enter-active { transition: all 0.5s var(--ease-spring); }
.slide-up-enter-from { opacity: 0; transform: translateY(40px) scale(0.95); }
.fade-up-enter-active { transition: all 0.3s ease; }
.fade-up-enter-from { opacity: 0; transform: translateY(10px); }
</style>
