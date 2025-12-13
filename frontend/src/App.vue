<script setup lang="ts">
import WorkspacePanel from "@/modules/workspace/ui/WorkspacePanel.vue";
import SettingsPanel from "@/modules/settings/ui/SettingsPanel.vue";
import PromptEditor from "@/modules/prompt-editor/ui/PromptEditor.vue";
import PromptTemplates from "@/modules/prompt-editor/ui/PromptTemplates.vue";
import GlobalToast from "@/shared/ui/toast/GlobalToast.vue";
import GlobalModal from "@/shared/ui/modal/GlobalModal.vue";
import { Icons } from "@/app/icons";
import { useAppController } from "@/app/controller";
const {
  activeTab,
  theme,
  statusText,
  loading,
  result,
  promptConfig,
  promptLoading,
  promptSaving,
  promptError,
  templateOptions,
  promptSettings,
  toggleTheme,
  updateConfig,
  updatePromptSettings,
  handleGrade,
  clearWorkspaceState,
  clearAllLocalCache,
  loadPromptConfig,
  handleSavePrompt,
  config,
} = useAppController();
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
          :class="{ active: activeTab === 'templates' }"
          @click="activeTab = 'templates'"
          v-tooltip="'提示词规范'"
        >
          <span class="icon" v-html="Icons.Templates"></span>
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
          <KeepAlive :include="['WorkspacePanel', 'PromptEditor', 'PromptTemplates', 'SettingsPanel']" :max="4">
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
            <PromptTemplates
              v-else-if="activeTab === 'templates'"
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
