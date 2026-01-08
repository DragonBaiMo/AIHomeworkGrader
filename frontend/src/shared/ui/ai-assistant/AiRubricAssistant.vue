<script setup lang="ts">
import { ref, computed } from "vue";
import { generateRubric } from "@/api/client";
import type { PromptCategory, RubricGenerateResponse } from "@/api/types";

const props = defineProps<{
  currentCategoryKey: string;
  currentCategoryName: string;
}>();

const emit = defineEmits<{
  (e: "apply", payload: { categoryKey: string; category: PromptCategory }): void;
}>();

const isOpen = ref(false);
const isLoading = ref(false);
const description = ref("");
const error = ref("");
const result = ref<RubricGenerateResponse | null>(null);

// 从 localStorage 获取模型配置
const modelConfig = computed(() => {
  const empty = { apiUrl: "", apiKey: "", modelName: "" };
  try {
    const primary = localStorage.getItem("ai-grader-pro-config");
    if (primary) {
      const cfg = JSON.parse(primary);
      return {
        apiUrl: cfg.apiUrl || "",
        apiKey: cfg.apiKey || "",
        modelName: cfg.modelName || "",
      };
    }
    const legacy = localStorage.getItem("grader_settings");
    if (legacy) {
      const settings = JSON.parse(legacy);
      return {
        apiUrl: settings.apiUrl || "",
        apiKey: settings.apiKey || "",
        modelName: settings.modelName || "",
      };
    }
  } catch {
    // ignore
  }
  return empty;
});

const hasModelConfig = computed(() => {
  const cfg = modelConfig.value;
  return Boolean(cfg.apiUrl && cfg.modelName);
});

const Icons = {
  Sparkles: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/><path d="M5 3v4"/><path d="M19 17v4"/><path d="M3 5h4"/><path d="M17 19h4"/></svg>`,
  X: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>`,
  Send: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>`,
  Check: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`,
  AlertCircle: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
};

function toggle() {
  isOpen.value = !isOpen.value;
  if (isOpen.value) {
    error.value = "";
    result.value = null;
  }
}

function close() {
  isOpen.value = false;
}

async function handleGenerate() {
  if (!description.value.trim()) {
    error.value = "请输入评分标准描述";
    return;
  }

  const cfg = modelConfig.value;
  if (!cfg.apiUrl || !cfg.modelName) {
    error.value = "请先在设置页填写模型接口";
    return;
  }

  isLoading.value = true;
  error.value = "";
  result.value = null;

  try {
    const resp = await generateRubric({
      description: description.value,
      api_url: cfg.apiUrl,
      api_key: cfg.apiKey,
      model_name: cfg.modelName,
    });
    result.value = resp;
  } catch (e) {
    error.value = (e as Error).message;
  } finally {
    isLoading.value = false;
  }
}

function handleApply() {
  if (!result.value) return;
  const rubric = result.value.rubric;
  emit("apply", {
    categoryKey: rubric.category_key || props.currentCategoryKey,
    category: {
      display_name: rubric.display_name,
      sections: rubric.sections,
      docx_validation: rubric.docx_validation,
    },
  });
  description.value = "";
  result.value = null;
  close();
}

function formatScore(sections: any[]) {
  return sections.reduce((sum, s) => sum + (s.max_score || 0), 0);
}
</script>

<template>
  <Teleport to="body">
    <!-- 悬浮按钮 -->
    <button
      class="ai-fab"
      :class="{ active: isOpen }"
      @click="toggle"
      title="AI 生成评分标准"
      :disabled="!hasModelConfig"
    >
      <span class="fab-content">
        <span class="fab-icon" v-html="Icons.Sparkles"></span>
      </span>
    </button>

    <!-- 对话弹窗 -->
    <Transition name="scale-fade">
      <div v-if="isOpen" class="ai-panel glass-panel">
        <!-- 头部 -->
        <div class="panel-header">
          <div class="header-main">
            <div class="ai-avatar">
              <span v-html="Icons.Sparkles"></span>
            </div>
            <div class="header-text">
              <h3 class="title">AI 评分标准助手</h3>
              <p class="subtitle">基于大模型一键生成结构化评分维度</p>
            </div>
          </div>
          <button class="icon-btn-close" @click="close">
            <span v-html="Icons.X"></span>
          </button>
        </div>

        <div class="panel-body custom-scrollbar">
          <!-- 上下文胶囊 -->
          <div class="context-capsule">
            <span class="capsule-label">当前分类</span>
            <span class="capsule-dot"></span>
            <span class="capsule-value">{{ currentCategoryName || '未选择' }}</span>
          </div>

          <!-- 警告栏 -->
          <div v-if="!hasModelConfig" class="status-banner warning">
            <span class="banner-icon" v-html="Icons.AlertCircle"></span>
            <span>请先在「设置」中配置模型 API 密钥</span>
          </div>

          <!-- 输入区域 -->
          <div class="input-wrapper">
            <textarea
              v-model="description"
              class="clean-textarea"
              placeholder="描述评分标准，例如：&#10;设计一个 Python 作业评分标准，满分 100 分，包含代码规范、功能实现、文档质量三个维度..."
              :disabled="isLoading"
              rows="4"
            ></textarea>
            <div class="textarea-footer">
              <span class="hint">建议明确指定“满分 xx 分”</span>
            </div>
          </div>

          <!-- 错误提示 -->
          <div v-if="error" class="status-banner error">
            {{ error }}
          </div>

          <!-- 结果预览卡片 -->
          <div v-if="result" class="result-card animate-in">
            <div class="result-summary">
              <span class="summary-label">生成预览</span>
              <span class="summary-badge">{{ result.total_score }} 分</span>
            </div>

            <div class="rubric-tree">
              <div class="tree-header">
                <span class="tree-title">{{ result.rubric.display_name }}</span>
              </div>
              <div class="tree-content">
                <div
                  v-for="(section, idx) in result.rubric.sections"
                  :key="idx"
                  class="tree-section"
                >
                  <div class="section-row">
                    <span class="section-name">{{ section.key }}</span>
                    <span class="score-pill">{{ section.max_score }}</span>
                  </div>
                  <div class="items-group">
                    <div
                      v-for="(item, iIdx) in section.items"
                      :key="iIdx"
                      class="item-row"
                    >
                      <span class="item-dot"></span>
                      <span class="item-name">{{ item.key }}</span>
                      <span class="item-score">{{ item.max_score }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 底部栏 -->
        <div class="panel-footer">
          <template v-if="!result">
            <button
              class="bento-btn primary full-width"
              :disabled="isLoading"
              @click="handleGenerate"
            >
              <span v-if="isLoading" class="loader-spinner-sm"></span>
              <span v-else v-html="Icons.Send"></span>
              <span>{{ isLoading ? '正在生成...' : '开始生成' }}</span>
            </button>
          </template>
          <template v-else>
            <button class="bento-btn ghost" @click="result = null">
              取消
            </button>
            <button class="bento-btn primary" @click="handleApply">
              <span v-html="Icons.Check"></span>
              应用标准
            </button>
          </template>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* --- Floating Action Button (Clean) --- */
.ai-fab {
  position: fixed;
  bottom: 32px;
  right: 32px;
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: var(--bg-panel);
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-float);
  cursor: pointer;
  z-index: 2147483647; /* Max Z-Index */
  pointer-events: auto;
  padding: 0;
  transition: all 0.3s var(--ease-spring);
  display: flex;
  align-items: center;
  justify-content: center;
}

.ai-fab:hover {
  transform: translateY(-4px) scale(1.05);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12);
  border-color: var(--brand);
}

.ai-fab:active {
  transform: scale(0.95);
}

.ai-fab.active {
  background: var(--brand);
  border-color: var(--brand);
  transform: rotate(15deg);
}

.fab-content {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--txt-primary);
  transition: color 0.3s;
}

.ai-fab.active .fab-content {
  color: #fff;
}

/* --- Main Panel (Clean Glass) --- */
.ai-panel {
  position: fixed;
  bottom: 100px;
  right: 32px;
  width: 400px;
  max-height: 600px;
  background: var(--bg-popover);
  border: 1px solid var(--border-light);
  border-radius: 20px;
  box-shadow: var(--shadow-float);
  display: flex;
  flex-direction: column;
  z-index: 2147483647; /* Max Z-Index */
  pointer-events: auto;
  transform-origin: bottom right;
  overflow: hidden;
}

/* Header */
.panel-header {
  padding: 20px 24px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  border-bottom: 1px solid var(--border-dim);
  background: var(--bg-glass);
}

.header-main {
  display: flex;
  gap: 12px;
}

.ai-avatar {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--brand) 0%, #8b5cf6 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 4px 12px rgba(var(--brand-rgb), 0.2);
  flex-shrink: 0;
}

.header-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.title {
  font-size: 15px;
  font-weight: 700;
  color: var(--txt-primary);
  line-height: 1.2;
}

.subtitle {
  font-size: 12px;
  color: var(--txt-tertiary);
  font-weight: 400;
}

.icon-btn-close {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  color: var(--txt-tertiary);
  background: transparent;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  margin-top: -4px;
  margin-right: -4px;
}

.icon-btn-close:hover {
  background: var(--bg-hover);
  color: var(--txt-primary);
}

/* Body */
.panel-body {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Capsule Context */
.context-capsule {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: var(--bg-hover);
  border-radius: 99px;
  border: 1px solid var(--border-dim);
  font-size: 12px;
  align-self: flex-start;
}

.capsule-label { color: var(--txt-tertiary); font-weight: 500; }
.capsule-dot { width: 4px; height: 4px; background: var(--border-focus); border-radius: 50%; }
.capsule-value { color: var(--txt-primary); font-weight: 600; }

/* Input */
.input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.clean-textarea {
  width: 100%;
  padding: 16px;
  background: var(--bg-app);
  border: 1px solid var(--border-dim);
  border-radius: 14px;
  font-size: 14px;
  color: var(--txt-primary);
  line-height: 1.6;
  resize: none;
  transition: all 0.2s;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);
}

.clean-textarea:focus {
  outline: none;
  border-color: var(--brand);
  background: var(--bg-panel);
  box-shadow: 0 0 0 3px var(--brand-dim);
}

.clean-textarea::placeholder { color: var(--txt-dim); }

.textarea-footer {
  display: flex;
  justify-content: flex-end;
}

.hint { font-size: 12px; color: var(--txt-tertiary); }

/* Status Banners */
.status-banner {
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-banner.warning {
  background: var(--warning-bg);
  color: var(--warning);
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.status-banner.error {
  background: var(--error-bg);
  color: var(--error);
  border: 1px solid rgba(244, 63, 94, 0.2);
}

/* Result Card */
.result-card {
  border: 1px solid var(--border-dim);
  border-radius: 16px;
  background: var(--bg-app);
  overflow: hidden;
}

.result-summary {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-dim);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg-table-head);
}

.summary-label { font-size: 12px; font-weight: 600; color: var(--txt-secondary); text-transform: uppercase; letter-spacing: 0.05em; }
.summary-badge {
  font-size: 12px; font-weight: 700; color: var(--brand);
  background: var(--brand-dim); padding: 2px 8px; border-radius: 6px;
}

.rubric-tree {
  padding: 16px;
}

.tree-title {
  font-size: 14px; font-weight: 600; color: var(--txt-primary);
  display: block; margin-bottom: 12px;
}

.tree-content { display: flex; flex-direction: column; gap: 12px; }

.tree-section {
  border: 1px solid var(--border-dim);
  border-radius: 10px;
  padding: 10px;
  background: var(--bg-panel);
}

.section-row {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 8px;
}

.section-name { font-size: 13px; font-weight: 600; color: var(--txt-primary); }
.score-pill { font-size: 12px; font-weight: 700; color: var(--txt-secondary); }

.items-group { display: flex; flex-direction: column; gap: 6px; }

.item-row {
  display: flex; align-items: center; gap: 8px;
  font-size: 12px; color: var(--txt-secondary);
}

.item-dot { width: 4px; height: 4px; background: var(--border-light); border-radius: 50%; }
.item-name { flex: 1; text-overflow: ellipsis; white-space: nowrap; overflow: hidden; }
.item-score { color: var(--txt-tertiary); font-family: 'JetBrains Mono'; }

/* Footer */
.panel-footer {
  padding: 20px 24px;
  background: var(--bg-glass);
  border-top: 1px solid var(--border-dim);
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.full-width { grid-column: 1 / -1; }

/* Transitions */
.scale-fade-enter-active,
.scale-fade-leave-active {
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.scale-fade-enter-from,
.scale-fade-leave-to {
  opacity: 0;
  transform: scale(0.95) translateY(10px);
}
</style>
