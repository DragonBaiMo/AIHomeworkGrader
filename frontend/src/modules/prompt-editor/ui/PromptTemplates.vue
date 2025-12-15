<script setup lang="ts">
import { ref, onMounted, computed, watch, nextTick } from "vue";
import { fetchPromptTemplates, savePromptTemplates, fetchPromptConfig, savePromptConfig } from "@/api/client";
import type { PromptConfig } from "@/api/types";
import { useUI } from "@/shared/composables/useUI";

const { showToast } = useUI();

const sections = ref<Record<string, string>>({});
const promptConfig = ref<PromptConfig | null>(null);
const loading = ref(false);
const saving = ref(false);
const activeSectionKey = ref("system");
const hasValidationErrors = ref(false);

const textareaRef = ref<HTMLTextAreaElement | null>(null);
const highlightRef = ref<HTMLPreElement | null>(null);

const REQUIRED_VARS: Record<string, string[]> = {
  rubric_user_template: ["{{RUBRIC_HUMAN_TEXT}}", "{{OUTPUT_SKELETON_JSON}}", "{{HOMEWORK_TEXT}}"],
  overall_comment_user: ["{{CATEGORY}}", "{{SCORE_TARGET_MAX}}", "{{AGG_SCORE}}", "{{MODEL_RESULTS_JSON}}"],
};

const VARIABLE_DESCRIPTIONS: Record<string, string> = {
  "{{RUBRIC_HUMAN_TEXT}}": "作业的评分标准，以人类可读的Markdown格式呈现。",
  "{{OUTPUT_SKELETON_JSON}}": "期望大模型输出的JSON结构骨架，包含所有评分维度和细则。",
  "{{HOMEWORK_TEXT}}": "学生提交的作业正文内容。",
  "{{CATEGORY}}": "当前作业的分类名称，如“职业规划书”。",
  "{{SCORE_TARGET_MAX}}": "本次批改的目标满分，例如 60 分。",
  "{{AGG_SCORE}}": "多个模型批改结果聚合后的总分（仅供参考）。",
  "{{MODEL_RESULTS_JSON}}": "包含所有模型批改结果的JSON字符串，可能包含失败记录。",
};

const SECTION_GROUPS = [
  {
    id: "global",
    title: "核心规范 (Global)",
    keys: ["system", "rubric_system_hard_rules", "overall_comment_system"],
  },
  {
    id: "templates",
    title: "通用模板 (Templates)",
    keys: ["rubric_user_template", "overall_comment_user"],
  },
];

const SECTION_META: Record<string, { label: string; desc: string; hint?: string }> = {
  system: {
    label: "AI 角色设定 (System)",
    desc: "定义 AI 在整个批改任务中的核心人设、语气与基本原则（最高优先级）。",
  },
  overall_comment_system: {
    label: "总体评语生成 (System)",
    desc: "定义生成“总体评语”时的系统指令、输出格式（JSON 结构）约束。",
  },
  overall_comment_user: {
    label: "总体评语模板 (User)",
    desc: "提供给 AI 的上下文模板，包含多模型结果汇总变量等。",
  },
  rubric_system_hard_rules: {
    label: "评分硬性规则 (System)",
    desc: "评分阶段的“宪法”，定义 JSON 输出格式 strict mode、安全规则与拒绝策略。",
  },
  rubric_user_template: {
    label: "评分任务模板 (User)",
    desc: "构建评分任务的最终 Prompt 骨架，包含评分标准与作业正文。",
    hint: "此模板需要包含以下变量：{{RUBRIC_HUMAN_TEXT}}、{{OUTPUT_SKELETON_JSON}}、{{HOMEWORK_TEXT}}。",
  },
};

const categoryKeys = computed(() => {
  if (!promptConfig.value) return [];
  return Object.keys(promptConfig.value.categories);
});

// 用于获取当前分类的目标满分
const currentScoreTarget = computed({
  get: () => {
    if (!promptConfig.value || !categoryKeys.value.includes(activeSectionKey.value)) return undefined;
    return promptConfig.value.categories[activeSectionKey.value]?.score_target_max;
  },
  set: (val: number | undefined) => {
    if (promptConfig.value && categoryKeys.value.includes(activeSectionKey.value)) {
      promptConfig.value.categories[activeSectionKey.value].score_target_max = val;
    }
  }
});

async function loadData() {
  loading.value = true;
  try {
    const [tpls, cfg] = await Promise.all([fetchPromptTemplates(), fetchPromptConfig()]);
    sections.value = tpls;
    promptConfig.value = cfg;
    
    // 确保默认选中第一个
    if (!activeSectionKey.value || !(sections.value[activeSectionKey.value] !== undefined || categoryKeys.value.includes(activeSectionKey.value))) {
      activeSectionKey.value = "system";
    }
    await nextTick(); // Ensure DOM is updated before syncing scroll
    syncScroll();
  } catch (e) {
    showToast((e as Error).message, "error");
  } finally {
    loading.value = false;
  }
}

function getCategoryLabel(key: string) {
  if (!promptConfig.value) return key;
  return promptConfig.value.categories[key]?.display_name || key;
}

function escapeHtml(text: string) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// 占位符高亮
const highlightedContent = computed(() => {
  const content = sections.value[activeSectionKey.value] || "";
  let safe = escapeHtml(content);
  
  // 高亮 {{...}} 变量
  safe = safe.replace(/\{\{([^}]+)\}\}/g, '<span class="variable-placeholder">{{$1}}</span>');
  // 高亮占位符提示文本
  safe = safe.replace(/（占位符：([^）]+)）/g, '<span class="hint-placeholder">（占位符：$1）</span>');
  
  // Handle trailing newline to match textarea behavior
  if (content.endsWith("\n")) {
    safe += "<br>";
  }
  
  return safe;
});

// 验证逻辑
const missingVars = computed(() => {
  const key = activeSectionKey.value;
  const content = sections.value[key] || "";
  
  let required: string[] = [];
  
  if (REQUIRED_VARS[key]) {
    required = REQUIRED_VARS[key];
  } else if (categoryKeys.value.includes(key)) {
    // 分类覆盖如果不是占位符，则需要包含 rubric_user_template 的核心变量
    if (!isPlaceholder(content)) {
      required = REQUIRED_VARS["rubric_user_template"];
    }
  }
  
  if (required.length === 0) return [];
  
  // 如果内容是占位符，则不校验
  if (isPlaceholder(content)) {
    return [];
  }
  
  return required.filter(v => !content.includes(v));
});

// 当前活跃模板的占位符说明
const placeholderHints = computed(() => {
  const key = activeSectionKey.value;
  let vars: string[] = [];

  if (REQUIRED_VARS[key]) {
    vars = REQUIRED_VARS[key];
  } else if (categoryKeys.value.includes(key)) {
    vars = REQUIRED_VARS["rubric_user_template"];
  }

  return vars.map(v => ({
    variable: v,
    description: VARIABLE_DESCRIPTIONS[v] || "未知变量"
  }));
});

watch(missingVars, (vars) => {
  hasValidationErrors.value = vars.length > 0;
});

watch(() => sections.value[activeSectionKey.value], () => {
  nextTick(syncScroll);
}, { flush: 'post' }); // Ensure DOM is updated before syncing

function syncScroll() {
  if (textareaRef.value && highlightRef.value) {
    highlightRef.value.scrollTop = textareaRef.value.scrollTop;
    highlightRef.value.scrollLeft = textareaRef.value.scrollLeft;
  }
}

async function handleSave() {
  if (missingVars.value.length > 0) {
    showToast(`无法保存：当前模板缺失必要变量 ${missingVars.value.join(", ")}`, "error");
    return;
  }
  
  saving.value = true;
  try {
    await savePromptTemplates(sections.value);
    
    // 如果是分类配置，同时保存 Config (针对 score_target_max 等字段)
    if (promptConfig.value && categoryKeys.value.includes(activeSectionKey.value)) {
       await savePromptConfig(promptConfig.value);
    }

    showToast("提示词规范与配置已保存", "success");
  } catch (e) {
    showToast((e as Error).message, "error");
  } finally {
    saving.value = false;
  }
}

function handleReset() {
  loadData();
}

function isPlaceholder(content: string) {
  return (content || "").trim().startsWith("（占位符：");
}

onMounted(() => {
  loadData();
});
</script>

<template>
  <div class="templates-layout">
    <div class="templates-sidebar custom-scrollbar">
      <div class="sidebar-header">
        <span class="sidebar-title">规范列表</span>
      </div>
      
      <div class="sidebar-content">
        <!-- Groups -->
        <div v-for="group in SECTION_GROUPS" :key="group.id" class="nav-group">
          <div class="group-title">{{ group.title }}</div>
          <div class="group-list">
             <button
              v-for="key in group.keys"
              :key="key"
              class="template-item"
              :class="{ active: activeSectionKey === key }"
              @click="activeSectionKey = key"
            >
              <div class="item-main">
                <span class="item-label">{{ SECTION_META[key]?.label || key }}</span>
              </div>
            </button>
          </div>
        </div>
        
        <!-- Categories -->
        <div class="nav-group" v-if="categoryKeys.length > 0">
           <div class="group-title">分类定制 (Overrides)</div>
           <div class="group-list">
             <button
              v-for="key in categoryKeys"
              :key="key"
              class="template-item"
              :class="{ active: activeSectionKey === key, 'is-placeholder': isPlaceholder(sections[key]) }"
              @click="activeSectionKey = key"
            >
              <div class="item-main">
                <span class="item-label">{{ getCategoryLabel(key) }}</span>
                <span v-if="isPlaceholder(sections[key])" class="badge-inherit">继承默认</span>
                <span v-else class="badge-custom">已定制</span>
              </div>
            </button>
        </div>
      </div>
    </div>

    </div>

    <div class="templates-editor">
      <div class="editor-toolbar">
        <div class="toolbar-info">
          <div class="title-row">
             <h3 class="current-title">
                {{ categoryKeys.includes(activeSectionKey) ? getCategoryLabel(activeSectionKey) : (SECTION_META[activeSectionKey]?.label || activeSectionKey) }}
             </h3>
             <div class="inline-target" v-if="promptConfig && categoryKeys.includes(activeSectionKey)">
                 <label>目标分</label>
                 <input 
                   type="number" 
                   class="clean-input-mini" 
                   v-model.number="currentScoreTarget" 
                   placeholder="-"
                   title="设置此分类的专属满分目标（如 100），留空则使用全局设置。"
                 >
             </div>
           </div>
           <p class="current-desc">{{ SECTION_META[activeSectionKey]?.desc || "自定义该分类的提示词模板（若为空或占位符，则自动继承通用模板）。" }}</p>
        </div>

        <div class="toolbar-actions">
           <button class="action-btn ghost" @click="handleReset" :disabled="saving || loading">
              重置
            </button>
           <button class="action-btn primary" @click="handleSave" :disabled="saving || loading || hasValidationErrors">
              {{ saving ? "保存中..." : "保存更改" }}
           </button>
        </div>
      </div>
      
      <div class="editor-content" v-if="activeSectionKey">
        <div class="editor-wrapper">
           <textarea
            ref="textareaRef"
            v-model="sections[activeSectionKey]"
            class="code-editor custom-scrollbar"
            :class="{ 'has-error': hasValidationErrors }"
            spellcheck="false"
            placeholder="在此输入 Markdown 内容..."
            @scroll="syncScroll"
            @input="syncScroll"
          ></textarea>
          <pre ref="highlightRef" class="highlight-overlay custom-scrollbar" v-html="highlightedContent"></pre>
        </div>

        <div class="validation-bar" v-if="missingVars.length > 0">
           <span class="error-icon">⚠️</span>
           <span class="error-text">当前模板缺失以下必要变量：
             <span v-for="(v, idx) in missingVars" :key="v">
               <code class="missing-var">{{ v }}</code><span v-if="idx < missingVars.length - 1">, </span>
             </span>
             。请补全后保存。
           </span>
        </div>
        
        <div class="editor-footer">
           <div class="hints-section" v-if="placeholderHints.length > 0">
             <div class="hint-item" v-for="hint in placeholderHints" :key="hint.variable">
               <code class="variable-name">{{ hint.variable }}</code>: {{ hint.description }}
             </div>
           </div>
           <span v-if="categoryKeys.includes(activeSectionKey) && isPlaceholder(sections[activeSectionKey])" class="footer-hint">
             当前内容为占位符，系统将自动使用 <b>rubric_user_template</b> 进行批改。
           </span>
           <span class="char-count">Length: {{ (sections[activeSectionKey] || "").length }}</span>
        </div>
      </div>
      
      <div v-else class="empty-state">
        <span v-if="loading" class="loader-spinner-sm black"></span>
        <span v-else>请选择左侧的提示词分段进行编辑</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.templates-layout {
  display: flex;
  width: 100%;
  height: 100%;
  background: var(--bg-app);
  overflow: hidden;
}

.templates-sidebar {
  width: 280px;
  flex-shrink: 0;
  background: var(--bg-panel);
  border-right: 1px solid var(--border-dim);
  display: flex;
  flex-direction: column;
}

@media (max-width: 900px) {
  .templates-sidebar { width: 220px; }
}
@media (max-width: 768px) {
  .templates-layout { flex-direction: column; }
  .templates-sidebar { width: 100%; height: 200px; border-right: none; border-bottom: 1px solid var(--border-dim); }
  .editor-toolbar { height: auto; padding: 16px; flex-wrap: wrap; gap: 12px; }
  .toolbar-actions { width: 100%; justify-content: flex-end; margin-left: 0; }
}

.sidebar-header {
  padding: 24px;
  border-bottom: 1px solid var(--border-dim);
}
.sidebar-title {
  font-size: 12px; font-weight: 800; color: var(--txt-tertiary);
  text-transform: uppercase; letter-spacing: 0.1em;
}

.sidebar-content {
  padding: 16px;
  display: flex; flex-direction: column; gap: 24px;
}

.nav-group { display: flex; flex-direction: column; gap: 8px; }
.group-title {
  font-size: 11px; font-weight: 700; color: var(--txt-tertiary);
  text-transform: uppercase; padding-left: 12px; margin-bottom: 4px;
}
.group-list { display: flex; flex-direction: column; gap: 4px; }

.template-item {
  text-align: left;
  background: transparent;
  border: 1px solid transparent;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}
.template-item:hover { background: var(--bg-hover); }
.template-item.active {
  background: var(--bg-active);
  border-color: var(--border-dim);
  box-shadow: 0 1px 4px rgba(0,0,0,0.02);
}

.item-main { display: flex; justify-content: space-between; align-items: center; width: 100%; }
.item-label {
  font-size: 13px; font-weight: 500; color: var(--txt-secondary);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 180px;
}
.template-item.active .item-label { color: var(--brand); font-weight: 600; }

.badge-inherit {
  font-size: 10px; color: var(--txt-tertiary); background: rgba(0,0,0,0.05);
  padding: 2px 6px; border-radius: 4px;
}
.badge-custom {
  font-size: 10px; color: var(--brand); background: rgba(var(--brand-rgb), 0.1);
  padding: 2px 6px; border-radius: 4px;
}

/* Editor Area */
.templates-editor {
  flex: 1;
  display: flex; flex-direction: column;
  background: var(--bg-app);
}

.editor-toolbar {
  height: 80px;
  padding: 0 32px;
  display: flex; justify-content: space-between; align-items: center;
  border-bottom: 1px solid var(--border-dim);
  background: var(--bg-panel);
}

.current-title { font-size: 16px; font-weight: 700; color: var(--txt-primary); }
.current-desc { font-size: 13px; color: var(--txt-tertiary); max-width: 600px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* Inline Target Input */
.title-row { display: flex; align-items: center; gap: 12px; margin-bottom: 4px; }
.inline-target {
  display: flex; align-items: center; gap: 6px;
  background: var(--bg-hover);
  padding: 2px 8px; border-radius: 6px;
  border: 1px solid var(--border-dim);
}
.inline-target label { font-size: 11px; color: var(--txt-tertiary); }
.clean-input-mini {
  width: 40px; background: transparent; border: none; 
  font-size: 12px; font-weight: 700; color: var(--brand);
  text-align: center; font-family: 'JetBrains Mono';
}
.clean-input-mini:focus { outline: none; }
.clean-input-mini::placeholder { color: var(--txt-quaternary); font-weight: 400; }

.toolbar-actions { display: flex; gap: 12px; margin-left: auto; }

/* Editor Content */
.editor-content {
  flex: 1;
  display: flex; flex-direction: column;
  padding: 24px 32px;
  overflow: hidden;
  gap: 16px;
}

.editor-wrapper {
  flex: 1;
  position: relative;
  display: flex; flex-direction: column;
}

.code-editor {
  flex: 1;
  background: transparent !important; /* Make it transparent to show overlay */
  border: 1px solid var(--border-dim);
  border-radius: 12px;
  padding: 20px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  line-height: 1.6;
  letter-spacing: 0; /* Explicitly set to avoid browser differences */
  color: var(--txt-primary);
  resize: none;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.01);
  transition: border-color 0.2s;
  position: absolute; /* Position over the overlay */
  top: 0; left: 0; right: 0; bottom: 0;
  width: 100%; height: 100%;
  overflow: auto;
  white-space: pre-wrap; /* Ensure wrapping like pre */
  word-break: break-all;
  z-index: 2; /* Bring textarea to front */
  caret-color: var(--brand); /* Custom caret color */
}
.code-editor:focus { outline: none; border-color: var(--brand); }
.code-editor.has-error { border-color: var(--error); background: rgba(var(--error-rgb), 0.02) !important; }

.highlight-overlay {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  width: 100%; height: 100%;
  background: var(--bg-panel); /* Background behind textarea */
  border: 1px solid var(--border-dim);
  border-radius: 12px;
  padding: 20px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  line-height: 1.6;
  letter-spacing: 0; /* Sync with textarea */
  color: transparent; /* Hide text */
  overflow: auto; /* Sync scroll with textarea */
  white-space: pre-wrap;
  word-break: break-all;
  pointer-events: none; /* Allow clicks to pass through */
  z-index: 1; /* Behind textarea */
  box-sizing: border-box; /* Include padding in width/height */
}

/* Scrollbar for transparent textarea and overlay */
.code-editor::-webkit-scrollbar, .highlight-overlay::-webkit-scrollbar { width: 8px; }
.code-editor::-webkit-scrollbar-thumb, .highlight-overlay::-webkit-scrollbar-thumb { background: rgba(120, 120, 120, 0.4); border-radius: 4px; }
.code-editor::-webkit-scrollbar-track, .highlight-overlay::-webkit-scrollbar-track { background: transparent; }


.variable-placeholder {
  /* color: transparent; Kept transparent to avoid ghosting */
  background: rgba(var(--brand-rgb), 0.2); /* More visible background */
  border-radius: 4px;
  color: transparent; 
  box-shadow: 0 0 0 1px rgba(var(--brand-rgb), 0.1); /* Subtle border for better definition */
}

.hint-placeholder {
  /* color: transparent; Kept transparent to avoid ghosting */
  background: rgba(var(--warning-rgb), 0.2);
  border-radius: 4px;
  color: transparent;
  box-shadow: 0 0 0 1px rgba(var(--warning-rgb), 0.1);
}

.validation-bar {
  display: flex; align-items: center; gap: 10px;
  background: rgba(var(--error-rgb), 0.1);
  border: 1px solid rgba(var(--error-rgb), 0.2);
  color: var(--error);
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 13px; font-weight: 600;
  animation: slideUp 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
}
.missing-var {
  font-family: 'JetBrains Mono', monospace;
  background: rgba(var(--error-rgb), 0.2);
  padding: 1px 4px;
  border-radius: 4px;
}

.editor-footer {
  display: flex; flex-direction: column; align-items: flex-start; gap: 10px;
  font-size: 12px; color: var(--txt-tertiary);
  font-family: 'JetBrains Mono';
  line-height: 1.5;
}
.hints-section {
  display: flex; flex-direction: column; gap: 5px;
  background: var(--bg-hover);
  border: 1px solid var(--border-dim);
  border-radius: 8px;
  padding: 10px 15px;
  width: 100%;
}
.hint-item {
  display: flex; align-items: flex-start; gap: 8px;
  color: var(--txt-secondary);
}
.variable-name {
  color: var(--brand);
  font-weight: 600;
}
.char-count { align-self: flex-end; margin-top: 5px; }
.footer-hint {
  width: 100%;
  text-align: right;
  color: var(--txt-tertiary);
}


.empty-state {
  flex: 1;
  display: flex; align-items: center; justify-content: center;
  color: var(--txt-tertiary);
}

/* Buttons */
.action-btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 8px 16px; border-radius: 10px;
  font-size: 13px; font-weight: 600; cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s;
}
.action-btn.ghost { background: transparent; color: var(--txt-secondary); }
.action-btn.ghost:hover { background: var(--bg-hover); color: var(--txt-primary); }
.action-btn.primary { background: var(--brand); color: #fff; }
.action-btn.primary:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(var(--brand-rgb), 0.3); }
.action-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; background: var(--bg-hover); color: var(--txt-tertiary); box-shadow: none; }

.loader-spinner-sm.black {
   border-color: rgba(0,0,0,0.1); border-top-color: var(--txt-primary);
}
</style>