<script setup lang="ts">
import { onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { fetchPromptConfig, gradeHomework, savePromptConfig } from "@/api/client";
import type { GradeConfigPayload, GradeResponse, PromptConfig, PromptSettings, TemplateOption } from "@/api/types";
import WorkspacePanel from "@/components/WorkspacePanel.vue";
import SettingsPanel from "@/components/SettingsPanel.vue";
import PromptEditor from "@/components/PromptEditor.vue";
import GlobalToast from "@/components/ui/GlobalToast.vue";
import GlobalModal from "@/components/ui/GlobalModal.vue";
import { useUI } from "@/composables/useUI";

// --- Icons (精选 SVG, 极简线条) ---
const Icons = {
  Logo: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2l9 4.9V17L12 22l-9-4.9V7z"/></svg>`,
  Workspace: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><path d="M9 3v18"/><path d="M3 9h18"/></svg>`,
  Rules: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><line x1="10" y1="9" x2="8" y2="9"/></svg>`,
  Settings: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>`,
  Moon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`,
  Sun: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`
};

type TabKey = "workspace" | "rules" | "settings";
type Theme = "dark" | "light";

const STORAGE_KEY = "ai-grader-pro-config";
const THEME_KEY = "ai-grader-theme";
const WORKSPACE_STATE_KEY = "ai-grader-workspace-state-v1";

const { showToast, confirm } = useUI();
const activeTab = ref<TabKey>("workspace");
const theme = ref<Theme>("dark");
const statusText = ref("就绪");
const loading = ref(false);
const gradeSessionId = ref(0);

type WorkspaceCachePayload = {
  version: 1;
  savedAt: number;
  inProgress: boolean;
  statusText: string;
  result: GradeResponse | null;
};

const config = reactive<GradeConfigPayload>({
  apiUrl: "",
  apiKey: "",
  modelName: "",
  multiEnabled: false,
  models: [],
  template: "auto",
  mock: false,
  skipFormatCheck: true,
  scoreTargetMax: 60,
});

const configPersistTimer = ref<number | null>(null);

const result = ref<GradeResponse | null>(null);
const promptConfig = ref<PromptConfig | null>(null);
const promptLoading = ref(false);
const promptSaving = ref(false);
const promptError = ref("");

const defaultTemplate: TemplateOption = {
  label: "自动识别",
  value: "auto",
};
const templateOptions = ref<TemplateOption[]>([defaultTemplate]);

const PROMPT_SETTINGS_KEY = "ai-grader-prompt-settings";
const promptSettings = reactive<PromptSettings>({
  autoSaveEnabled: true,
  autoSaveIntervalSeconds: 60,
});

function updateConfig(payload: Partial<GradeConfigPayload>) {
  Object.assign(config, payload);
}

function updatePromptSettings(payload: Partial<PromptSettings>) {
  if (typeof payload.autoSaveEnabled === "boolean") {
    promptSettings.autoSaveEnabled = payload.autoSaveEnabled;
  }
  if (typeof payload.autoSaveIntervalSeconds === "number" && payload.autoSaveIntervalSeconds > 0) {
    promptSettings.autoSaveIntervalSeconds = payload.autoSaveIntervalSeconds;
  }
}

function loadPromptSettings() {
  const cache = localStorage.getItem(PROMPT_SETTINGS_KEY);
  if (!cache) return;
  try {
    const parsed = JSON.parse(cache) as PromptSettings;
    promptSettings.autoSaveEnabled = parsed.autoSaveEnabled ?? promptSettings.autoSaveEnabled;
    if (parsed.autoSaveIntervalSeconds && parsed.autoSaveIntervalSeconds > 0) {
      promptSettings.autoSaveIntervalSeconds = parsed.autoSaveIntervalSeconds;
    }
  } catch {
    /* ignore */
  }
}

function sanitizeResultForCache(payload: GradeResponse): GradeResponse {
  return {
    ...payload,
    items: (payload.items || []).map((item) => ({
      ...item,
      raw_response: null,
    })),
  };
}

function persistWorkspaceState(inProgress: boolean) {
  const payload: WorkspaceCachePayload = {
    version: 1,
    savedAt: Date.now(),
    inProgress,
    statusText: statusText.value,
    result: result.value ? sanitizeResultForCache(result.value) : null,
  };
  try {
    localStorage.setItem(WORKSPACE_STATE_KEY, JSON.stringify(payload));
  } catch {
    showToast("批改结果过大，无法缓存到本地存储。", "warning");
  }
}

function clearWorkspaceState() {
  result.value = null;
  statusText.value = "就绪";
  localStorage.removeItem(WORKSPACE_STATE_KEY);
}

function loadWorkspaceState() {
  const cache = localStorage.getItem(WORKSPACE_STATE_KEY);
  if (!cache) return;
  try {
    const parsed = JSON.parse(cache) as WorkspaceCachePayload;
    if (parsed.version !== 1) return;
    if (parsed.result) result.value = parsed.result;
    if (typeof parsed.statusText === "string" && parsed.statusText.trim()) {
      statusText.value = parsed.statusText;
    }
    if (parsed.inProgress) {
      statusText.value = "上次批改在页面刷新时被中断，请重新点击开始批改。";
      showToast(statusText.value, "warning");
      persistWorkspaceState(false);
    }
  } catch {
    /* ignore */
  }
}

// --- Theme Logic ---
function toggleTheme() {
  theme.value = theme.value === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", theme.value);
  localStorage.setItem(THEME_KEY, theme.value);
}

function initTheme() {
  const saved = localStorage.getItem(THEME_KEY) as Theme | null;
  if (saved) {
    theme.value = saved;
  } else {
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    theme.value = prefersDark ? "dark" : "light";
  }
  document.documentElement.setAttribute("data-theme", theme.value);
}

// --- Logic: Restore Config ---
function loadFromStorage() {
  const cache = localStorage.getItem(STORAGE_KEY);
  if (!cache) return;
  try {
    const saved = JSON.parse(cache) as Partial<GradeConfigPayload>;
    updateConfig({
      apiUrl: saved.apiUrl || "",
      apiKey: saved.apiKey || "",
      modelName: saved.modelName || "",
      multiEnabled: Boolean(saved.multiEnabled),
      models: Array.isArray(saved.models) && saved.models.length
        ? saved.models.map((m: any) => ({
            api_url: String(m?.api_url || ""),
            api_key: String(m?.api_key || ""),
            model_name: String(m?.model_name || ""),
          }))
        : [],
      template: saved.template || defaultTemplate.value,
      mock: Boolean(saved.mock),
      skipFormatCheck: saved.skipFormatCheck !== false,
      scoreTargetMax: typeof saved.scoreTargetMax === "number" ? saved.scoreTargetMax : 60,
    });
  } catch { /* ignore */ }
}

watch(
  () => ({ ...config }),
  (val) => {
    if (configPersistTimer.value !== null) {
      window.clearTimeout(configPersistTimer.value);
    }
    configPersistTimer.value = window.setTimeout(() => {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(val));
      configPersistTimer.value = null;
    }, 200);
  },
  { deep: true },
);

watch(
  () => ({ ...promptSettings }),
  (val) => {
    localStorage.setItem(PROMPT_SETTINGS_KEY, JSON.stringify(val));
  },
  { deep: true },
);

onBeforeUnmount(() => {
  if (configPersistTimer.value !== null) {
    window.clearTimeout(configPersistTimer.value);
    configPersistTimer.value = null;
  }
});

// --- Logic: Prompt Config ---
async function loadPromptConfig() {
  promptLoading.value = true;
  try {
    const cfg = await fetchPromptConfig();
    if (!cfg) {
      promptConfig.value = {
        system_prompt: "",
        categories: {
          default: {
            display_name: "默认分类",
            sections: [],
            docx_validation: {
              enabled: false,
              allowed_font_keywords: [],
              allowed_font_size_pts: [],
              font_size_tolerance: 0.5,
              target_line_spacing: null,
              line_spacing_tolerance: null,
            },
          },
        },
      };
      promptError.value = "提示词配置为空，已加载默认配置";
      rebuildTemplateOptions(promptConfig.value);
      showToast(promptError.value, "warning");
      return;
    }
    promptConfig.value = cfg;
    rebuildTemplateOptions(cfg);
  } catch (err) {
    promptError.value = (err as Error).message;
    rebuildTemplateOptions(null);
  } finally {
    promptLoading.value = false;
  }
}

function rebuildTemplateOptions(cfg: PromptConfig | null) {
  if (!cfg) {
    templateOptions.value = [defaultTemplate];
    if (!config.template) config.template = defaultTemplate.value;
    return;
  }
  const list = Object.entries(cfg.categories).map(([key, cat]) => ({
    label: cat.display_name || key,
    value: key,
  }));
  templateOptions.value = [defaultTemplate, ...(list.length ? list : [])];
  
  if (!templateOptions.value.some((t) => t.value === config.template)) {
    config.template = templateOptions.value[0].value;
  }
}

async function handleGrade(files: File[]) {
  if (loading.value) return;
  const currentSession = bumpGradeSession();
  loading.value = true;
  statusText.value = "处理中";
  persistWorkspaceState(true);
  try {
    const resp = await gradeHomework(files, config);
    if (currentSession !== gradeSessionId.value) return;
    result.value = resp;
    statusText.value = "已完成";
    persistWorkspaceState(false);
    showToast(`批改完成！成功处理 ${resp.success_count} 个文件`, "success");
  } catch (err) {
    if (currentSession !== gradeSessionId.value) return;
    statusText.value = "异常";
    persistWorkspaceState(false);
    showToast((err as Error).message, "error");
  } finally {
    if (currentSession !== gradeSessionId.value) return;
    loading.value = false;
  }
}

async function handleSavePrompt(payload: PromptConfig) {
  promptSaving.value = true;
  try {
    await savePromptConfig(payload);
    promptConfig.value = payload;
    rebuildTemplateOptions(payload);
    showToast("配置已保存", "success");
  } catch (err) {
    showToast((err as Error).message, "error");
  } finally {
    promptSaving.value = false;
  }
}

function bumpGradeSession(): number {
  gradeSessionId.value += 1;
  return gradeSessionId.value;
}

function resetConfigToDefaults() {
  updateConfig({
    apiUrl: "",
    apiKey: "",
    modelName: "",
    multiEnabled: false,
    models: [],
    template: defaultTemplate.value,
    mock: false,
    skipFormatCheck: true,
    scoreTargetMax: 60,
  });
}

function resetPromptSettingsToDefaults() {
  promptSettings.autoSaveEnabled = true;
  promptSettings.autoSaveIntervalSeconds = 60;
}

function clearAllLocalCache() {
  confirm({
    title: "清除本地缓存",
    content: "确定要清除批改缓存吗？这将清空当前批改结果与工作台状态（不影响系统设置与规则编辑器设置），且无法恢复。",
    confirmText: "立即清除",
    type: "danger",
    onConfirm: () => {
      executeClearCache();
    }
  });
}

function executeClearCache() {
  bumpGradeSession();
  loading.value = false;
  statusText.value = "就绪";
  result.value = null;

  try {
    localStorage.removeItem(WORKSPACE_STATE_KEY);
  } catch {
    /* ignore */
  }
  showToast("批改缓存已清除", "success");
}

onMounted(() => {
  initTheme();
  loadFromStorage();
  loadPromptSettings();
  loadWorkspaceState();
  loadPromptConfig();
});
</script>

<template>
  <div class="app-shell">
    <!-- Navigation Rail -->
    <nav class="nav-rail glass-morphism">
      <div class="nav-section top">
        <div class="brand-orb">
          <div class="orb-core"></div>
          <div class="orb-glow"></div>
        </div>
      </div>

      <div class="nav-section middle">
        <button
          class="nav-item"
          :class="{ active: activeTab === 'workspace' }"
          @click="activeTab = 'workspace'"
          v-tooltip="'工作台'"
        >
          <span class="icon" v-html="Icons.Workspace"></span>
        </button>

        <button
          class="nav-item"
          :class="{ active: activeTab === 'rules' }"
          @click="activeTab = 'rules'"
          v-tooltip="'规则编辑器'"
        >
          <span class="icon" v-html="Icons.Rules"></span>
        </button>

        <button
          class="nav-item"
          :class="{ active: activeTab === 'settings' }"
          @click="activeTab = 'settings'"
          v-tooltip="'系统设置'"
        >
          <span class="icon" v-html="Icons.Settings"></span>
        </button>
      </div>

      <div class="nav-section bottom">
        <div class="system-pill">
          <button class="theme-btn" @click="toggleTheme">
            <span class="icon" v-if="theme === 'dark'" v-html="Icons.Moon"></span>
            <span class="icon" v-else v-html="Icons.Sun"></span>
          </button>
          <div class="divider"></div>
          <div class="status-indicator" :class="{ 'is-busy': loading, 'is-error': statusText === '异常' }">
            <div class="dot"></div>
          </div>
        </div>
      </div>
    </nav>

    <!-- Main Viewport -->
    <main class="main-viewport">
      <div class="viewport-content custom-scrollbar">
        <Transition name="page-transition" mode="out-in">
          <KeepAlive :include="['WorkspacePanel', 'PromptEditor', 'SettingsPanel']" :max="3">
            <WorkspacePanel 
              v-if="activeTab === 'workspace'"
              :config="config"
              :templates="templateOptions"
              :loading="loading"
              :result="result"
              :status-text="statusText"
              @submit="handleGrade"
              @clear-result="clearWorkspaceState"
              @clear-all-cache="clearAllLocalCache"
              @request-settings="activeTab = 'settings'"
              @update:config="updateConfig"
            />
            <SettingsPanel 
              v-else-if="activeTab === 'settings'"
              :config="config"
              :prompt-settings="promptSettings"
              @update:config="updateConfig"
              @update:promptSettings="updatePromptSettings"
              @submit="activeTab = 'workspace'"
            />
            <PromptEditor 
              v-else
              :config="promptConfig"
              :loading="promptLoading"
              :saving="promptSaving"
              :error="promptError"
              :auto-save-enabled="promptSettings.autoSaveEnabled"
              :auto-save-interval-ms="promptSettings.autoSaveIntervalSeconds * 1000"
              @refresh="loadPromptConfig"
              @save="handleSavePrompt"
            />
          </KeepAlive>
        </Transition>
      </div>
    </main>

    <GlobalToast />
    <GlobalModal />
  </div>
</template>

<style scoped>
/* --- App Shell --- */
.app-shell {
  display: flex;
  height: 100vh;
  width: 100vw;
  background-color: var(--bg-app);
  overflow: hidden;
  position: relative;
}

/* --- Navigation Rail --- */
.nav-rail {
  width: 72px;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  padding: 32px 0;
  border-right: 1px solid var(--border-dim);
  z-index: 50;
  flex-shrink: 0;
  background: var(--bg-panel);
  backdrop-filter: blur(20px);
}

.nav-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  width: 100%;
}

/* Brand Orb */
.brand-orb {
  position: relative;
  width: 40px; height: 40px;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 8px;
}
.orb-core {
  width: 10px; height: 10px; border-radius: 50%;
  background: var(--brand);
  z-index: 2;
  box-shadow: 0 0 16px var(--brand);
}
.orb-glow {
  position: absolute; inset: 0;
  border-radius: 50%;
  border: 1px solid var(--border-light);
  opacity: 0.3;
  animation: breathe 6s ease-in-out infinite;
}
@keyframes breathe {
  0%, 100% { transform: scale(0.85); opacity: 0.2; }
  50% { transform: scale(1.1); opacity: 0.5; }
}

/* Nav Items */
.nav-item {
  position: relative;
  width: 44px; height: 44px;
  border-radius: 12px;
  background: transparent;
  border: 1px solid transparent;
  color: var(--txt-tertiary);
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s cubic-bezier(0.2, 0.8, 0.2, 1);
}
.nav-item:hover {
  background: var(--bg-hover);
  color: var(--txt-primary);
  transform: translateY(-1px);
}
.nav-item.active {
  background: var(--bg-active);
  color: var(--brand);
  border-color: var(--border-dim);
  box-shadow: 0 4px 12px -2px rgba(0,0,0,0.1);
}
.nav-item.active::after {
  content: ''; position: absolute;
  left: -14px; top: 10px; bottom: 10px; width: 3px;
  background: var(--brand);
  border-radius: 0 4px 4px 0;
  box-shadow: 0 0 8px var(--brand);
}

/* System Pill */
.system-pill {
  display: flex; flex-direction: column; align-items: center; gap: 16px;
  padding: 12px 6px;
  background: var(--bg-active);
  border-radius: 99px;
  border: 1px solid var(--border-dim);
}
.theme-btn {
  width: 32px; height: 32px;
  border-radius: 50%;
  border: none; background: transparent;
  color: var(--txt-secondary);
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
}
.theme-btn:hover { background: var(--bg-hover); color: var(--txt-primary); }

.divider { width: 20px; height: 1px; background: var(--border-dim); }

.status-indicator {
  width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
}
.dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--success);
  box-shadow: 0 0 8px var(--success-bg);
  transition: all 0.3s;
}
.status-indicator.is-busy .dot {
  background: var(--brand);
  box-shadow: 0 0 12px var(--brand-glow);
  animation: pulse-dot 1.5s infinite;
}
.status-indicator.is-error .dot {
  background: var(--error);
  box-shadow: 0 0 12px var(--error-bg);
}
@keyframes pulse-dot {
  0% { transform: scale(0.8); opacity: 0.6; }
  50% { transform: scale(1.4); opacity: 1; }
  100% { transform: scale(0.8); opacity: 0.6; }
}

/* --- Viewport --- */
.main-viewport {
  flex: 1;
  position: relative;
  overflow: hidden;
  background: radial-gradient(circle at top left, var(--bg-panel) 0%, var(--bg-app) 40%);
}

.viewport-content {
  width: 100%; height: 100%;
  padding: 40px;
  overflow-y: auto;
  overflow-x: hidden;
}

/* Transitions */
.page-transition-enter-active,
.page-transition-leave-active {
  transition: opacity 0.15s cubic-bezier(0.2, 0.8, 0.2, 1), transform 0.15s cubic-bezier(0.2, 0.8, 0.2, 1);
  will-change: opacity, transform;
}
.page-transition-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.page-transition-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* Mobile */
@media (max-width: 768px) {
  .app-shell { flex-direction: column-reverse; }
  .nav-rail {
    width: 100%; height: 72px; flex-direction: row;
    padding: 0 24px; border-right: none; border-top: 1px solid var(--border-dim);
  }
  .nav-section.top { display: none; }
  .nav-section.middle { flex-direction: row; justify-content: center; gap: 32px; }
  .nav-item.active::after {
    left: 50%; top: auto; bottom: -18px; width: 24px; height: 3px;
    transform: translateX(-50%); border-radius: 4px 4px 0 0;
  }
  .nav-section.bottom { width: auto; }
  .system-pill { flex-direction: row; padding: 4px 12px; }
  .divider { width: 1px; height: 16px; }
  
  .viewport-content { padding: 20px; }
}
</style>
