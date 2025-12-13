<script setup lang="ts">
import { computed, ref, watch } from "vue";
import type { GradeConfigPayload, GradeResponse, TemplateOption } from "@/api/types";
import { useUI } from "@/composables/useUI";

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
  (e: "clear-result"): void;
  (e: "clear-all-cache"): void;
}>();

const { showToast } = useUI();

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
  updateConfigField("template", val);
  isTemplateOpen.value = false;
}

function closeDropdown() {
  isTemplateOpen.value = false;
}

const Icons = {
  Upload: `<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="M12 12v9"/><path d="m16 16-4-4-4 4"/></svg>`,
  Doc: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>`,
  Check: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`,
  Download: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>`,
  Trash: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>`,
  Alert: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
  ChevronDown: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>`,
  Search: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>`
};

const fileSummary = computed(() => {
  if (!files.value.length) return "";
  const total = files.value.length;
  const sizeMB = files.value.reduce((acc, cur) => acc + cur.size, 0) / 1024 / 1024;
  return `${total} 个文件 (${sizeMB.toFixed(1)} MB)`;
});

const detailCache = new Map<string, any>();

watch(
  () => props.result?.items,
  () => {
    detailCache.clear();
  },
);

const parsedItems = computed(() => {
  const items = props.result?.items || [];
  return items.map((item) => {
    const cacheKey = `${item.file_name}@@${item.detail_json || ""}`;
    let parsed = detailCache.get(cacheKey);
    if (!parsed) {
      let detail: any = {};
      try {
        detail = item.detail_json ? JSON.parse(item.detail_json) : {};
      } catch {
        detail = {};
      }
      parsed = {
        rubric_items: detail.rubric_items || [],
        feedback: detail.feedback || item.comment || "",
        error_message: item.error_message || detail.error,
        display_score: typeof detail.total_score === "number" ? detail.total_score : item.score,
      };
      detailCache.set(cacheKey, parsed);
    }
    return { ...item, ...parsed };
  });
});

const parsedFilteredItems = computed(() => {
  const items = parsedItems.value;
  const query = (resultQuery.value || "").trim().toLowerCase();
  return items.filter((item) => {
    if (resultFilter.value === "success" && item.status !== "成功") return false;
    if (resultFilter.value === "fail" && item.status === "成功") return false;
    if (!query) return true;
    const hay = `${item.file_name} ${item.student_id || ""} ${item.student_name || ""}`.toLowerCase();
    return hay.includes(query);
  });
});

function getScoreClass(score: number | null | undefined) {
  if (score === null || score === undefined) return "";
  const max = Number(props.config?.scoreTargetMax || 0);
  const percent = max > 0 ? (score / max) * 100 : score;
  if (percent >= 90) return "score-high";
  if (percent >= 60) return "score-mid";
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

function onDragOver() {
  if (!dragOver.value) dragOver.value = true;
}

function onDragLeave() {
  if (dragOver.value) dragOver.value = false;
}

function handleSubmit() {
  if (!files.value.length) return;
  if (!props.config.mock && !props.config.apiUrl) {
    emit("request-settings");
    return;
  }
  emit("submit", files.value);
}

function downloadResultExcel() {
  const url = props.result?.download_result_url;
  if (!url) {
    showToast("暂无可下载的成绩表，请先完成一次批改。", "warning");
    return;
  }
  window.location.href = url;
}

function clearResult() {
  emit("clear-result");
}

function clearAllCache() {
  emit("clear-all-cache");
}

function updateConfigField<T extends keyof GradeConfigPayload>(key: T, value: GradeConfigPayload[T]) {
  emit("update:config", { [key]: value } as Partial<GradeConfigPayload>);
}
</script>

<template>
  <div class="workspace-layout">
    <!-- Header: Simple Title -->
    <header class="workspace-header">
      <div class="header-titles">
        <h1 class="page-title">智能批改台</h1>
        <p class="page-subtitle">AI Automated Assessment System</p>
      </div>

      <div class="header-actions">
        <button class="bento-btn danger" type="button" @click="clearAllCache">一键清除缓存</button>
      </div>
    </header>

    <!-- Main Stage: Split Layout -->
    <section class="main-stage">
      <!-- Left: Upload Zone (Square) -->
      <div class="stage-left">
        <div
          class="drop-zone-card"
          :class="{ 
            'is-dragover': dragOver, 
            'has-files': files.length > 0,
            'is-processing': loading 
          }"
          @dragover.prevent="onDragOver"
          @dragleave="onDragLeave"
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
              <h3 v-else class="zone-title">拖拽文件至此</h3>
              
              <p v-if="!loading" class="zone-subtitle">支持 Word / Markdown / Text 格式</p>
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
      </div>

      <!-- Right: Control Panel -->
      <div class="stage-right">
        <!-- Template Card -->
        <div class="control-card template-card" :class="{ 'is-active': isTemplateOpen }">
          <div class="card-label">评估模板</div>
          <div class="bento-select full-width" :class="{ active: isTemplateOpen }">
            <button 
              class="select-trigger" 
              @click="isTemplateOpen = !isTemplateOpen"
            >
              <span class="selected-text">{{ currentTemplateLabel }}</span>
              <span class="trigger-icon" v-html="Icons.ChevronDown"></span>
            </button>

            <Transition name="dropdown-anim">
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
            
            <div v-if="isTemplateOpen" class="backdrop-click" @click="closeDropdown"></div>
          </div>
          <p class="card-desc">选择适用的评分标准与规则集</p>
        </div>

        <!-- Mode Card -->
        <div class="control-card mode-card">
           <div class="card-header-row">
             <div class="card-label">模拟模式</div>
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
           </div>
           <p class="card-desc">开启后将使用模拟数据进行演示，不消耗 Token。</p>
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
                <button class="bento-icon-btn" title="下载 Excel" @click="downloadResultExcel">
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
              <div class="th col-action">展开</div>
            </div>

            <!-- List Items -->
            <div class="table-rows">
              <TransitionGroup name="list">
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
                      <div
                        class="score-pill"
                        :class="getScoreClass(item.display_score)"
                        :title="`目标分：${item.display_score ?? '-'} / ${config.scoreTargetMax}；规则分：${item.score_rubric ?? '-'} / ${item.score_rubric_max ?? '-'}`"
                      >
                        <span class="status-dot" :class="getScoreClass(item.display_score) === 'score-high' ? 'ok' : getScoreClass(item.display_score) === 'score-low' ? 'err' : 'warn'"></span>
                        <span class="score-val">{{ item.display_score ?? '-' }}</span>
                        <span class="score-max" v-if="item.display_score !== null">/{{ config.scoreTargetMax }}</span>
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
                      <div v-if="item.grader_results && item.grader_results.length" class="model-result-panel">
                        <div class="model-result-title">
                          多模型批改明细
                        </div>
                        <div class="model-result-sub">
                          聚合算法：{{ item.aggregate_strategy || 'mean' }} &nbsp;|&nbsp; 汇总分：{{ item.display_score ?? '-' }} / {{ config.scoreTargetMax }} &nbsp;|&nbsp; 总体评语：多模型下主模型二次生成
                        </div>
                          <div class="model-result-table">
                            <div class="model-result-row header">
                              <div class="c-name">模型</div>
                              <div class="c-url">接口地址</div>
                              <div class="c-score">分数</div>
                              <div class="c-lat">耗时</div>
                              <div class="c-status">状态</div>
                              <div class="c-err">异常信息</div>
                            </div>
                            <div v-for="(m, mi) in item.grader_results" :key="mi" class="model-result-row">
                              <div class="c-name" :title="m.model_name">{{ m.model_name || `模型${m.model_index || (mi + 1)}` }}</div>
                              <div class="c-url" :title="m.api_url || ''">{{ m.api_url || '-' }}</div>
                              <div class="c-score">{{ m.score ?? '-' }}</div>
                              <div class="c-lat">{{ m.latency_ms ? `${m.latency_ms}ms` : '-' }}</div>
                              <div class="c-status">
                                <span class="status-dot" :class="m.status === '成功' ? 'ok' : 'err'"></span>
                                {{ m.status || '-' }}
                              </div>
                              <div class="c-err" :title="m.error_message || ''">{{ m.error_message || '-' }}</div>
                            </div>
                          </div>
                        </div>
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
              </TransitionGroup>
              
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

<style scoped src="./workspace-panel.css"></style>
