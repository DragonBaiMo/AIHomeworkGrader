<script setup lang="ts">
import { onMounted, reactive, ref, watch } from "vue";
import { fetchPromptConfig, gradeHomework, savePromptConfig } from "@/api/client";
import type { GradeConfigPayload, GradeResponse, PromptConfig, TemplateOption } from "@/api/types";
import WorkspacePanel from "@/components/WorkspacePanel.vue";
import SettingsPanel from "@/components/SettingsPanel.vue";
import PromptEditor from "@/components/PromptEditor.vue";
import GlobalToast from "@/components/ui/GlobalToast.vue";
import GlobalModal from "@/components/ui/GlobalModal.vue";
import { useUI } from "@/composables/useUI";

// --- Icons (精选 SVG, 极简线条) ---
const Icons = {
  Logo: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>`,
  Workspace: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="9" y1="21" x2="9" y2="9"></line></svg>`,
  Rules: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>`,
  Settings: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>`,
  Moon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`,
  Sun: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`
};

type TabKey = "workspace" | "rules" | "settings";
type Theme = "dark" | "light";

const STORAGE_KEY = "ai-grader-pro-config";
const THEME_KEY = "ai-grader-theme";

const { showToast } = useUI();
const activeTab = ref<TabKey>("workspace");
const theme = ref<Theme>("dark");
const statusText = ref("就绪");
const loading = ref(false);

const config = reactive<GradeConfigPayload>({
  apiUrl: "",
  apiKey: "",
  modelName: "",
  template: "auto",
  mock: false,
  skipFormatCheck: true,
  scoreTargetMax: 60,
});

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

function updateConfig(payload: Partial<GradeConfigPayload>) {
  Object.assign(config, payload);
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
      template: saved.template || defaultTemplate.value,
      mock: Boolean(saved.mock),
      skipFormatCheck: saved.skipFormatCheck !== false,
      scoreTargetMax: typeof saved.scoreTargetMax === "number" ? saved.scoreTargetMax : 60,
    });
  } catch { /* ignore */ }
}

watch(
  () => ({ ...config }),
  (val) => localStorage.setItem(STORAGE_KEY, JSON.stringify(val)),
  { deep: true },
);

// --- Logic: Prompt Config ---
async function loadPromptConfig() {
  promptLoading.value = true;
  try {
    const cfg = await fetchPromptConfig();
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
  loading.value = true;
  statusText.value = "处理中";
  try {
    const resp = await gradeHomework(files, config);
    result.value = resp;
    statusText.value = "已完成";
    showToast(`批改完成！成功处理 ${resp.success_count} 个文件`, "success");
  } catch (err) {
    statusText.value = "异常";
    showToast((err as Error).message, "error");
  } finally {
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

onMounted(() => {
  initTheme();
  loadFromStorage();
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
          <KeepAlive include="WorkspacePanel">
            <WorkspacePanel 
              v-if="activeTab === 'workspace'"
              :config="config"
              :templates="templateOptions"
              :loading="loading"
              :result="result"
              :status-text="statusText"
              @submit="handleGrade"
              @request-settings="activeTab = 'settings'"
              @update:config="updateConfig"
            />
            <SettingsPanel 
              v-else-if="activeTab === 'settings'"
              :config="config"
              @update:config="updateConfig"
              @submit="activeTab = 'workspace'"
            />
            <PromptEditor 
              v-else
              :config="promptConfig"
              :loading="promptLoading"
              :saving="promptSaving"
              :error="promptError"
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
  width: 80px;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  padding: 32px 0;
  border-right: 1px solid var(--border-dim);
  z-index: 50;
  flex-shrink: 0;
  background: var(--bg-panel); /* Fallback */
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
}
.orb-core {
  width: 12px; height: 12px; border-radius: 50%;
  background: var(--brand);
  z-index: 2;
  box-shadow: 0 0 20px var(--brand);
}
.orb-glow {
  position: absolute; inset: 0;
  border-radius: 50%;
  border: 1px solid var(--border-light);
  opacity: 0.5;
  animation: breathe 4s ease-in-out infinite;
}
@keyframes breathe {
  0%, 100% { transform: scale(0.8); opacity: 0.3; }
  50% { transform: scale(1.1); opacity: 0.6; border-color: var(--brand-dim); }
}

/* Nav Items */
.nav-item {
  position: relative;
  width: 48px; height: 48px;
  border-radius: 14px;
  background: transparent;
  border: 1px solid transparent;
  color: var(--txt-tertiary);
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.3s cubic-bezier(0.25, 1, 0.5, 1);
}
.nav-item:hover {
  background: var(--bg-hover);
  color: var(--txt-secondary);
  transform: scale(1.05);
}
.nav-item.active {
  background: var(--bg-active);
  color: var(--brand);
  border-color: var(--border-dim);
  box-shadow: 
    0 4px 12px -2px rgba(0,0,0,0.1), 
    inset 0 0 0 1px rgba(255,255,255,0.05);
}
.nav-item.active::after {
  content: ''; position: absolute;
  left: -17px; top: 12px; bottom: 12px; width: 3px;
  background: var(--brand);
  border-radius: 0 4px 4px 0;
  box-shadow: 0 0 10px var(--brand);
}

/* System Pill */
.system-pill {
  display: flex; flex-direction: column; align-items: center; gap: 12px;
  padding: 12px 8px;
  background: var(--bg-active);
  border-radius: 20px;
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

.divider { width: 24px; height: 1px; background: var(--border-dim); }

.status-indicator {
  width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
}
.dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--success);
  box-shadow: 0 0 8px var(--success-bg);
  transition: all 0.3s;
}
.status-indicator.is-busy .dot {
  background: var(--brand);
  box-shadow: 0 0 12px var(--brand-glow);
  animation: pulse-dot 1s infinite;
}
.status-indicator.is-error .dot {
  background: var(--error);
  box-shadow: 0 0 12px var(--error-bg);
}
@keyframes pulse-dot {
  0% { transform: scale(0.8); opacity: 0.6; }
  50% { transform: scale(1.2); opacity: 1; }
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
  transition: opacity 0.3s var(--ease-out), transform 0.3s var(--ease-spring);
}
.page-transition-enter-from {
  opacity: 0;
  transform: scale(0.98) translateY(10px);
}
.page-transition-leave-to {
  opacity: 0;
  transform: scale(1.02);
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