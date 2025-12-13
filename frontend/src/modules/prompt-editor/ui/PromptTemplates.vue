<script setup lang="ts">
import { ref, onMounted, computed, watch } from "vue";
import { fetchPromptTemplates, savePromptTemplates, fetchPromptConfig } from "@/api/client";
import type { PromptConfig } from "@/api/types";
import { useUI } from "@/shared/composables/useUI";

const { showToast } = useUI();

const sections = ref<Record<string, string>>({});
const promptConfig = ref<PromptConfig | null>(null);
const loading = ref(false);
const saving = ref(false);
const activeSectionKey = ref("system");
const hasValidationErrors = ref(false);

const REQUIRED_VARS: Record<string, string[]> = {
  rubric_user_template: ["{{RUBRIC_HUMAN_TEXT}}", "{{OUTPUT_SKELETON_JSON}}", "{{HOMEWORK_TEXT}}"],
  overall_comment_user: ["{{MODEL_RESULTS_JSON}}"],
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

const SECTION_META: Record<string, { label: string; desc: string }> = {
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
  },
};

const categoryKeys = computed(() => {
  if (!promptConfig.value) return [];
  return Object.keys(promptConfig.value.categories);
});

async function loadData() {
  loading.value = true;
  try {
    const [tpls, cfg] = await Promise.all([fetchPromptTemplates(), fetchPromptConfig()]);
    sections.value = tpls;
    promptConfig.value = cfg;
    
    // 确保默认选中第一个
    if (!activeSectionKey.value) {
      activeSectionKey.value = "system";
    }
  } catch (e) {
    showToast((e as Error).message, "error");
  } finally {
    loading.value = false;
  }
}

// 验证逻辑
const missingVars = computed(() => {
  const key = activeSectionKey.value;
  const content = sections.value[key] || "";
  
  // 如果是分类覆盖（override），则它也必须包含 User Template 的核心变量
  // 或者是默认模板，我们也检查
  let required: string[] = [];
  
  if (REQUIRED_VARS[key]) {
    required = REQUIRED_VARS[key];
  } else if (categoryKeys.value.includes(key)) {
    // 分类覆盖也被视为 rubric_user_template 的变体
    required = REQUIRED_VARS["rubric_user_template"];
  }
  
  if (required.length === 0) return [];
  
  // 如果内容是占位符，则不校验（因为运行时会回退到默认模板）
  if (content.trim().startsWith("（占位符：")) {
    return [];
  }
  
  return required.filter(v => !content.includes(v));
});

watch(missingVars, (vars) => {
  hasValidationErrors.value = vars.length > 0;
});


async function handleSave() {
  if (missingVars.value.length > 0) {
    showToast(`无法保存：当前模板缺失必要变量 ${missingVars.value.join(", ")}`, "error");
    return;
  }
  
  saving.value = true;
  try {
    await savePromptTemplates(sections.value);
    showToast("提示词规范已保存", "success");
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

function getCategoryLabel(key: string) {
  if (!promptConfig.value) return key;
  return promptConfig.value.categories[key]?.display_name || key;
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
          <h3 class="current-title">
             {{ categoryKeys.includes(activeSectionKey) ? getCategoryLabel(activeSectionKey) : (SECTION_META[activeSectionKey]?.label || activeSectionKey) }}
          </h3>
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
            v-model="sections[activeSectionKey]"
            class="code-editor custom-scrollbar"
            :class="{ 'has-error': hasValidationErrors }"
            spellcheck="false"
            placeholder="在此输入 Markdown 内容..."
          ></textarea>
        </div>

        <div class="validation-bar" v-if="missingVars.length > 0">
           <span class="error-icon">⚠️</span>
           <span class="error-text">缺失必要变量：{{ missingVars.join(", ") }}</span>
        </div>
        
        <div class="editor-footer">
           <div class="hints">
             <span v-if="categoryKeys.includes(activeSectionKey) && isPlaceholder(sections[activeSectionKey])">
               当前内容为占位符，系统将自动使用 <b>rubric_user_template</b> 进行批改。
             </span>
           </div>
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
  width: 300px;
  background: var(--bg-panel);
  border-right: 1px solid var(--border-dim);
  display: flex;
  flex-direction: column;
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

.current-title { font-size: 16px; font-weight: 700; color: var(--txt-primary); margin-bottom: 4px; }
.current-desc { font-size: 13px; color: var(--txt-tertiary); max-width: 600px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.toolbar-actions { display: flex; gap: 12px; }

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
  background: var(--bg-panel);
  border: 1px solid var(--border-dim);
  border-radius: 12px;
  padding: 20px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  line-height: 1.6;
  color: var(--txt-primary);
  resize: none;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.01);
  transition: border-color 0.2s;
}
.code-editor:focus { outline: none; border-color: var(--brand); }
.code-editor.has-error { border-color: var(--error); background: rgba(var(--error-rgb), 0.02); }

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
@keyframes slideUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

.editor-footer {
  display: flex; justify-content: space-between; align-items: center;
  font-size: 12px; color: var(--txt-tertiary);
  font-family: 'JetBrains Mono';
}
.hints b { color: var(--txt-secondary); }

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