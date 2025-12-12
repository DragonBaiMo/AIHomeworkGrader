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

// --- Icons ---
const Icons = {
  Logo: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="currentColor" stroke-width="2"/><path d="M8 12L11 15L16 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  Workspace: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>`,
  Rules: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>`,
  Settings: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>`,
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
    <!-- Responsive Navigation: Rail on Desktop, Tab Bar on Mobile -->
    <nav class="responsive-nav glass">
      <!-- Logo (Desktop Only) -->
      <div class="nav-logo desktop-only">
        <div class="logo-icon" v-html="Icons.Logo"></div>
      </div>

      <!-- Nav Items -->
      <div class="nav-menu">
        <button 
          class="nav-item" 
          :class="{ active: activeTab === 'workspace' }"
          @click="activeTab = 'workspace'"
          title="工作台"
        >
          <span class="icon" v-html="Icons.Workspace"></span>
          <span class="label mobile-only">工作台</span>
        </button>
        
        <button 
          class="nav-item" 
          :class="{ active: activeTab === 'rules' }"
          @click="activeTab = 'rules'"
          title="评分规则"
        >
          <span class="icon" v-html="Icons.Rules"></span>
          <span class="label mobile-only">规则</span>
        </button>
        
        <button 
          class="nav-item" 
          :class="{ active: activeTab === 'settings' }"
          @click="activeTab = 'settings'"
          title="设置"
        >
          <span class="icon" v-html="Icons.Settings"></span>
          <span class="label mobile-only">设置</span>
        </button>
      </div>

      <!-- Bottom Actions -->
      <div class="nav-actions">
        <button class="nav-item theme-btn" @click="toggleTheme">
          <span class="icon" v-if="theme === 'dark'" v-html="Icons.Moon"></span>
          <span class="icon" v-else v-html="Icons.Sun"></span>
        </button>

        <div class="status-wrapper">
          <div 
            class="status-indicator" 
            :class="{ 
              'is-loading': loading, 
              'is-error': statusText === '异常' 
            }" 
          ></div>
        </div>
      </div>
    </nav>

    <!-- Main Content Area -->
    <main class="main-content">
      <div class="content-container">
        <Transition name="fade-scale" mode="out-in">
          <KeepAlive include="WorkspacePanel">
            <component 
              :is="activeTab === 'workspace' ? WorkspacePanel : activeTab === 'settings' ? SettingsPanel : PromptEditor"
              :config="activeTab === 'rules' ? promptConfig : config"
              :templates="templateOptions"
              :loading="loading || promptLoading"
              :result="result"
              :status-text="statusText"
              :saving="promptSaving"
              :error="promptError"
              @submit="handleGrade"
              @request-settings="activeTab = 'settings'"
              @update:config="updateConfig"
              @refresh="loadPromptConfig"
              @save="handleSavePrompt"
            />
          </KeepAlive>
        </Transition>
      </div>
    </main>

    <!-- Global UI Layers -->
    <GlobalToast />
    <GlobalModal />
  </div>
</template>

<style scoped>
/* Layout Architecture */
.app-shell {
  display: flex;
  height: 100vh;
  width: 100vw;
  background-color: var(--bg-app);
  overflow: hidden;
}

/* --- Responsive Nav --- */
.responsive-nav {
  display: flex;
  flex-direction: column;
  z-index: 50;
  flex-shrink: 0;
  border-right: 1px solid var(--border-dim);
  width: 68px; /* Desktop width */
  height: 100%;
  align-items: center;
  padding: 24px 0;
}

/* Logo */
.nav-logo {
  margin-bottom: 40px;
  color: var(--brand);
}
.logo-icon svg { width: 28px; height: 28px; }

/* Menu */
.nav-menu {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
  width: 100%;
  align-items: center;
}

.nav-item {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: transparent;
  border: none;
  color: var(--txt-tertiary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s var(--ease-out);
  position: relative;
  flex-direction: column; /* For mobile label */
}

.nav-item:hover {
  background: var(--bg-hover);
  color: var(--txt-secondary);
}

.nav-item.active {
  background: var(--bg-active);
  color: var(--txt-primary);
  box-shadow: inset 0 0 0 1px var(--border-light);
}

/* Desktop Indicator */
.responsive-nav .nav-item.active::before {
  content: '';
  position: absolute;
  left: -12px;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 20px;
  background: var(--brand);
  border-radius: 0 4px 4px 0;
  box-shadow: 0 0 8px var(--brand-glow);
}

/* Actions */
.nav-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}
.status-wrapper { padding: 8px; }
.status-indicator {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--success);
  box-shadow: 0 0 5px var(--success-bg);
  transition: all 0.3s;
}
.status-indicator.is-loading {
  background: var(--brand);
  box-shadow: 0 0 8px var(--brand-glow);
  animation: pulse 1.5s infinite;
}

/* --- Mobile / Small Screen Styles --- */
.mobile-only { display: none; }

@media (max-width: 768px) {
  .app-shell {
    flex-direction: column-reverse; /* Bottom Nav */
  }

  .responsive-nav {
    width: 100%;
    height: 64px; /* Bottom Bar Height */
    flex-direction: row;
    border-right: none;
    border-top: 1px solid var(--border-dim);
    padding: 0 16px;
    justify-content: space-between;
  }

  .desktop-only { display: none; }
  
  .nav-menu {
    flex-direction: row;
    justify-content: space-around;
    height: 100%;
    gap: 0;
  }

  .nav-item {
    width: auto;
    height: 100%;
    flex: 1;
    border-radius: 0;
    gap: 4px;
  }
  
  .nav-item .icon svg { width: 24px; height: 24px; }
  .label.mobile-only { display: block; font-size: 10px; font-weight: 500; }

  /* Mobile Active State */
  .responsive-nav .nav-item.active {
    background: transparent;
    color: var(--brand);
    box-shadow: none;
  }
  .responsive-nav .nav-item.active::before {
    /* Top indicator for bottom tab */
    left: 50%;
    top: 0;
    transform: translateX(-50%);
    width: 24px;
    height: 3px;
    border-radius: 0 0 4px 4px;
  }

  .nav-actions {
    flex-direction: row;
    gap: 8px;
    margin-left: 8px;
  }
  .theme-btn { width: 40px; }
}

/* Main Content */
.main-content {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.content-container {
  height: 100%;
  width: 100%;
  padding: 32px 40px;
  overflow-y: auto;
  overflow-x: hidden;
  max-width: 1400px;
  margin: 0 auto;
}

@media (max-width: 768px) {
  .content-container {
    padding: 20px 16px; /* Less padding on mobile */
  }
}

/* Transitions */
.fade-scale-enter-active,
.fade-scale-leave-active {
  transition: opacity 0.3s var(--ease-out), transform 0.3s var(--ease-out);
}

.fade-scale-enter-from {
  opacity: 0;
  transform: scale(0.99) translateY(10px);
}
.fade-scale-leave-to {
  opacity: 0;
  transform: scale(1.01);
}

@keyframes pulse {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.4); opacity: 0.6; }
  100% { transform: scale(1); opacity: 1; }
}
</style>
