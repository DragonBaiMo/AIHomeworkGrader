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
  <div class="app-layout">
    <!-- Sidebar / Rail -->
    <nav class="glass nav-rail">
      <div class="nav-top">
        <div class="brand-logo" v-html="Icons.Logo"></div>
      </div>

      <div class="nav-middle">
        <button 
          class="nav-btn" 
          :class="{ active: activeTab === 'workspace' }"
          @click="activeTab = 'workspace'"
          title="工作台"
        >
          <span class="icon" v-html="Icons.Workspace"></span>
        </button>
        
        <button 
          class="nav-btn" 
          :class="{ active: activeTab === 'rules' }"
          @click="activeTab = 'rules'"
          title="评分规则"
        >
          <span class="icon" v-html="Icons.Rules"></span>
        </button>
        
        <button 
          class="nav-btn" 
          :class="{ active: activeTab === 'settings' }"
          @click="activeTab = 'settings'"
          title="设置"
        >
          <span class="icon" v-html="Icons.Settings"></span>
        </button>
      </div>

      <div class="nav-bottom">
        <button class="nav-btn theme-toggle" @click="toggleTheme">
          <span class="icon" v-if="theme === 'dark'" v-html="Icons.Moon"></span>
          <span class="icon" v-else v-html="Icons.Sun"></span>
        </button>
        
        <div class="status-dot" :class="{ 'busy': loading, 'error': statusText === '异常' }"></div>
      </div>
    </nav>

    <!-- Content Area -->
    <main class="main-viewport">
      <div class="viewport-inner">
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

    <GlobalToast />
    <GlobalModal />
  </div>
</template>

<style scoped>
/* Layout Grid */
.app-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  background-color: var(--bg-app);
  overflow: hidden;
}

/* --- Nav Rail --- */
.nav-rail {
  width: 72px;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px 0;
  border-right: 1px solid var(--border-dim);
  z-index: 50;
  flex-shrink: 0;
}

.nav-top { margin-bottom: 40px; }
.brand-logo { 
  color: var(--brand); 
  filter: drop-shadow(0 0 12px var(--brand-glow));
  animation: float 6s ease-in-out infinite;
}

.nav-middle {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
  align-items: center;
}

.nav-btn {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-m);
  background: transparent;
  border: none;
  color: var(--txt-tertiary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s var(--ease-spring);
  position: relative;
}

.nav-btn:hover {
  background: var(--bg-hover);
  color: var(--txt-secondary);
  transform: scale(1.05);
}

.nav-btn.active {
  background: var(--bg-active);
  color: var(--brand);
  box-shadow: inset 0 0 0 1px var(--border-light);
}

/* Active Indicator */
.nav-btn.active::before {
  content: '';
  position: absolute;
  left: -14px;
  width: 4px;
  height: 20px;
  background: var(--brand);
  border-radius: 0 4px 4px 0;
  box-shadow: 0 0 12px var(--brand);
}

.nav-bottom {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}

.status-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--success);
  box-shadow: 0 0 8px var(--success-bg);
  transition: all 0.3s;
}
.status-dot.busy {
  background: var(--brand);
  box-shadow: 0 0 12px var(--brand-glow);
  animation: pulse 1.5s infinite;
}
.status-dot.error { background: var(--error); box-shadow: 0 0 12px var(--error-bg); }

/* --- Main Viewport --- */
.main-viewport {
  flex: 1;
  position: relative;
  overflow: hidden;
  /* 这里的 padding 配合 content-container 形成悬浮感 */
  padding: 16px; 
}

.viewport-inner {
  width: 100%;
  height: 100%;
  border-radius: var(--radius-l);
  /* 内层不设背景，让组件自己画卡片，或者统一在这里画一个大卡片背景 */
  overflow-y: auto;
  overflow-x: hidden;
  padding: 24px;
  scroll-behavior: smooth;
}

/* 适配移动端 */
@media (max-width: 768px) {
  .app-layout { flex-direction: column-reverse; }
  .nav-rail {
    width: 100%; height: 64px; flex-direction: row;
    padding: 0 24px; border-right: none; border-top: 1px solid var(--border-dim);
    justify-content: space-between;
  }
  .nav-top, .brand-logo { display: none; }
  .nav-middle { flex-direction: row; height: 100%; justify-content: center; gap: 32px; }
  .nav-btn.active::before {
    left: 50%; top: -14px; transform: translateX(-50%);
    width: 20px; height: 4px; border-radius: 0 0 4px 4px;
  }
  .nav-bottom { flex-direction: row; gap: 16px; margin-left: 0; }
  
  .main-viewport { padding: 0; }
  .viewport-inner { border-radius: 0; padding: 16px; }
}

/* Animations */
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}
@keyframes pulse {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.4); opacity: 0.5; }
  100% { transform: scale(1); opacity: 1; }
}

.fade-scale-enter-active, .fade-scale-leave-active {
  transition: opacity 0.4s var(--ease-out), transform 0.4s var(--ease-spring);
}
.fade-scale-enter-from { opacity: 0; transform: scale(0.98) translateY(10px); }
.fade-scale-leave-to { opacity: 0; transform: scale(1.02); }
</style>