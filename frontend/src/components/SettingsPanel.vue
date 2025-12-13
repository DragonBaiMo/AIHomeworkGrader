<script setup lang="ts">
import { ref } from "vue";
import type { GradeConfigPayload, PromptSettings } from "@/api/types";

const props = defineProps<{
  config: GradeConfigPayload;
  promptSettings: PromptSettings;
}>();

const emit = defineEmits<{
  (e: "update:config", payload: Partial<GradeConfigPayload>): void;
  (e: "update:promptSettings", payload: Partial<PromptSettings>): void;
  (e: "submit"): void;
}>();

const localConfig = ref({ ...props.config });

const Icons = {
  Server: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"/><rect x="2" y="14" width="20" height="8" rx="2" ry="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>`,
  Key: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/></svg>`,
  Cpu: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"/><path d="M9 9h6v6H9z"/><path d="M9 1v3"/><path d="M15 1v3"/><path d="M9 20v3"/><path d="M15 20v3"/><path d="M20 9h3"/><path d="M20 15h3"/><path d="M1 9h3"/><path d="M1 15h3"/></svg>`,
  Check: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`,
  Plus: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>`,
  Trash: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>`
};

function handleChange<T extends keyof GradeConfigPayload>(key: T, value: GradeConfigPayload[T]) {
  localConfig.value[key] = value;
  emit("update:config", { [key]: value });
}

function handleToggleMulti(enabled: boolean) {
  handleChange("multiEnabled", enabled as any);
  if (enabled) {
    const models = Array.isArray(localConfig.value.models) ? [...localConfig.value.models] : [];
    if (models.length === 0) {
      models.push({ api_url: "", api_key: "", model_name: "" });
      localConfig.value.models = models;
      emit("update:config", { models });
    }
  }
}

function handleModelChange(index: number, key: "api_url" | "api_key" | "model_name", value: string) {
  const models = Array.isArray(localConfig.value.models) ? [...localConfig.value.models] : [];
  while (models.length <= index) {
    models.push({ api_url: "", api_key: "", model_name: "" });
  }
  const current = { ...(models[index] as any) };
  current[key] = value;
  models[index] = current;
  localConfig.value.models = models;
  emit("update:config", { models });
}

function addModelRow() {
  const models = Array.isArray(localConfig.value.models) ? [...localConfig.value.models] : [];
  if (models.length >= 2) return;
  models.push({ api_url: "", api_key: "", model_name: "" });
  localConfig.value.models = models;
  emit("update:config", { models });
}

function removeModelRow(index: number) {
  const models = Array.isArray(localConfig.value.models) ? [...localConfig.value.models] : [];
  if (models.length <= 1) return;
  models.splice(index, 1);
  localConfig.value.models = models;
  emit("update:config", { models });
} 

function handlePromptSetting<T extends keyof PromptSettings>(key: T, value: PromptSettings[T]) {
  emit("update:promptSettings", { [key]: value });
}
</script>

<template>
  <div class="settings-layout animate-in">
    <div class="settings-container bento-grid">
      
      <!-- Main Settings Card -->
      <div class="settings-card main-config bento-grid-item">
        <header class="card-header">
          <div class="header-icon">
            <span v-html="Icons.Server"></span>
          </div>
          <div class="header-info">
            <h2 class="card-title">系统连接</h2>
            <p class="card-desc">配置核心模型服务</p>
          </div>
          <button class="save-btn" @click="emit('submit')">
            <span v-html="Icons.Check"></span>
            <span>保存</span>
          </button>
        </header>

        <div class="card-body">
          <div class="input-grid">
            <div class="input-group full">
              <label class="field-label">API 端点 <span class="sub">Base URL</span></label>
              <div class="input-wrapper">
                <input 
                  type="text" 
                  class="modern-input" 
                  :value="localConfig.apiUrl"
                  @input="handleChange('apiUrl', ($event.target as HTMLInputElement).value)"
                  placeholder="https://api.openai.com/v1"
                />
                <div class="focus-ring"></div>
              </div>
            </div>

            <div class="input-group half">
              <label class="field-label">API 密钥 <span class="sub">Secret Key</span></label>
              <div class="input-wrapper">
                <input 
                  type="password" 
                  class="modern-input" 
                  :value="localConfig.apiKey"
                  @input="handleChange('apiKey', ($event.target as HTMLInputElement).value)"
                  placeholder="sk-..."
                />
                <div class="focus-ring"></div>
              </div>
            </div>

            <div class="input-group half">
              <label class="field-label">模型名称 <span class="sub">Model Name</span></label>
              <div class="input-wrapper">
                <input 
                  type="text" 
                  class="modern-input" 
                  :value="localConfig.modelName"
                  @input="handleChange('modelName', ($event.target as HTMLInputElement).value)"
                  placeholder="gpt-4o"
                />
                <div class="focus-ring"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Multi Model Card -->
      <div class="settings-card multi-config bento-grid-item">
        <div class="card-body">
          <div class="toggle-row">
            <div class="toggle-info">
              <span class="toggle-title">多模型共识评估</span>
              <span class="toggle-desc">至少 1 个模型成功=本文件成功；最终分=成功模型平均分；多模型下会用主模型二次生成总体评语（JSON）</span>
            </div>
            <label class="ios-switch">
              <input
                type="checkbox"
                :checked="localConfig.multiEnabled"
                @change="handleToggleMulti(($event.target as HTMLInputElement).checked)"
              />
              <div class="switch-track">
                <div class="switch-thumb"></div>
              </div>
            </label>
          </div>

          <div v-if="localConfig.multiEnabled" class="model-list-container">
            <div class="list-label">辅助模型节点</div>
            <div class="model-list">
              <div v-for="(m, idx) in (localConfig.models || [])" :key="idx" class="model-item-card">
                <div class="model-item-header">
                  <span class="model-tag">Model {{ idx + 1 }}</span>
                  <button 
                    v-if="(localConfig.models || []).length > 1" 
                    class="icon-btn danger" 
                    type="button" 
                    @click="removeModelRow(idx)"
                  >
                    <span v-html="Icons.Trash"></span>
                  </button>
                </div>
                <div class="model-inputs">
                  <input
                    type="text"
                    class="mini-input"
                    :value="m.api_url"
                    @input="handleModelChange(idx, 'api_url', ($event.target as HTMLInputElement).value)"
                    placeholder="API 地址"
                  />
                  <input
                    type="password"
                    class="mini-input"
                    :value="m.api_key"
                    @input="handleModelChange(idx, 'api_key', ($event.target as HTMLInputElement).value)"
                    placeholder="API 密钥"
                  />
                  <input
                    type="text"
                    class="mini-input"
                    :value="m.model_name"
                    @input="handleModelChange(idx, 'model_name', ($event.target as HTMLInputElement).value)"
                    placeholder="模型名称"
                  />
                </div>
              </div>
            </div>

            <button
              v-if="(localConfig.models || []).length < 2"
              class="add-model-btn"
              type="button"
              @click="addModelRow"
            >
              <span v-html="Icons.Plus"></span>
              <span>添加模型</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Advanced / Misc -->
      <div class="settings-card misc-config bento-grid-item">
        <div class="card-body">
          <div class="toggle-row">
            <div class="toggle-info">
              <span class="toggle-title">模拟运行模式</span>
              <span class="toggle-desc">使用本地随机数据生成结果，不消耗 Token</span>
            </div>
            <label class="ios-switch">
              <input 
                type="checkbox" 
                :checked="localConfig.mock"
                @change="handleChange('mock', ($event.target as HTMLInputElement).checked)"
              />
              <div class="switch-track">
                <div class="switch-thumb"></div>
              </div>
            </label>
          </div>

          <div class="divider"></div>

          <div class="toggle-row">
            <div class="toggle-info">
              <span class="toggle-title">自动保存规则</span>
              <span class="toggle-desc">编辑提示词时自动同步</span>
            </div>
            <div class="row-actions">
              <div class="input-wrapper small" v-if="promptSettings.autoSaveEnabled">
                 <input
                  type="number"
                  class="modern-input center"
                  min="15"
                  step="15"
                  :value="promptSettings.autoSaveIntervalSeconds"
                  @input="handlePromptSetting('autoSaveIntervalSeconds', Number(($event.target as HTMLInputElement).value) || 60)"
                />
                <span class="unit">s</span>
              </div>
              <label class="ios-switch">
                <input
                  type="checkbox"
                  :checked="promptSettings.autoSaveEnabled"
                  @change="handlePromptSetting('autoSaveEnabled', ($event.target as HTMLInputElement).checked)"
                />
                <div class="switch-track">
                  <div class="switch-thumb"></div>
                </div>
              </label>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.settings-layout {
  display: flex;
  justify-content: center;
  padding: 40px 20px;
  width: 100%;
  height: 100%;
}

.settings-container {
  display: flex;
  flex-direction: column;
  gap: 32px;
  width: 100%;
  max-width: 640px;
}

/* Header */
.settings-header {
  margin-bottom: 8px;
  padding: 0 4px;
}
.header-titles .page-title {
  font-size: 32px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--txt-primary);
  margin-bottom: 8px;
  background: linear-gradient(180deg, #fff 0%, var(--txt-secondary) 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
[data-theme="light"] .header-titles .page-title {
  background: linear-gradient(180deg, var(--txt-primary) 0%, var(--txt-tertiary) 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
.header-titles .page-subtitle {
  font-size: 13px;
  color: var(--txt-tertiary);
  font-weight: 500;
  letter-spacing: 0.05em;
  font-family: 'JetBrains Mono', monospace;
  opacity: 0.8;
}

/* Cards */
.settings-card {
  background: var(--bg-panel);
  border-radius: 24px;
  border: 1px solid var(--border-dim);
  box-shadow: var(--shadow-card);
  overflow: hidden;
  transition: transform 0.3s var(--ease-out), box-shadow 0.3s;
}
.settings-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-float);
  border-color: var(--border-light);
}

/* Header */
.card-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px 24px 20px 24px;
  border-bottom: 1px solid var(--border-dim);
  background: var(--bg-app);
}
.header-icon {
  width: 44px; height: 44px;
  border-radius: 12px;
  background: var(--bg-panel);
  border: 1px solid var(--border-dim);
  display: flex; align-items: center; justify-content: center;
  color: var(--brand);
  box-shadow: var(--shadow-subtle);
}
.header-info { flex: 1; }
.card-title { font-size: 16px; font-weight: 700; color: var(--txt-primary); margin-bottom: 2px; }
.card-desc { font-size: 12px; color: var(--txt-tertiary); }

.save-btn {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 20px;
  background: var(--brand);
  color: #fff;
  border-radius: 10px;
  font-weight: 600;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(var(--brand-rgb), 0.25);
}
.save-btn:hover {
  background: var(--brand-hover);
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(var(--brand-rgb), 0.35);
}
.save-btn:active { transform: translateY(1px); }

/* Body */
.card-body { padding: 24px; display: flex; flex-direction: column; gap: 24px; }

/* Inputs */
.input-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}
.input-group.full { grid-column: 1 / -1; }
.input-group { display: flex; flex-direction: column; gap: 8px; }

.field-label {
  font-size: 12px; font-weight: 600; color: var(--txt-secondary);
  display: flex; justify-content: space-between;
}
.field-label .sub { font-weight: 400; color: var(--txt-tertiary); font-family: 'JetBrains Mono'; opacity: 0.8; }

.input-wrapper { position: relative; width: 100%; }
.modern-input {
  width: 100%;
  padding: 12px 14px;
  background: var(--bg-app);
  border: 1px solid var(--border-dim);
  border-radius: 10px;
  color: var(--txt-primary);
  font-size: 14px;
  font-family: 'JetBrains Mono', monospace;
  transition: all 0.2s;
}
.modern-input:focus {
  border-color: var(--brand);
  background: var(--bg-panel);
  box-shadow: 0 0 0 3px var(--brand-dim);
}
.modern-input::placeholder { color: var(--txt-tertiary); opacity: 0.5; }

/* Toggles */
.toggle-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 4px 0;
}
.toggle-info { display: flex; flex-direction: column; gap: 4px; }
.toggle-title { font-size: 14px; font-weight: 600; color: var(--txt-primary); }
.toggle-desc { font-size: 12px; color: var(--txt-tertiary); max-width: 300px; line-height: 1.4; }

/* Switch */
.ios-switch { position: relative; width: 44px; height: 24px; cursor: pointer; flex-shrink: 0; }
.ios-switch input { display: none; }
.switch-track {
  width: 100%; height: 100%;
  background: var(--bg-app);
  border-radius: 99px;
  border: 1px solid var(--border-dim);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
}
.switch-thumb {
  position: absolute; top: 2px; left: 2px;
  width: 18px; height: 18px;
  background: var(--txt-secondary);
  border-radius: 50%;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.ios-switch input:checked + .switch-track { background: var(--brand); border-color: var(--brand); }
.ios-switch input:checked + .switch-track .switch-thumb { transform: translateX(20px); background: #fff; }

.divider { height: 1px; background: var(--border-dim); width: 100%; }

/* Multi Model List */
.model-list-container {
  display: flex; flex-direction: column; gap: 16px;
  animation: slideDown 0.3s var(--ease-out);
  background: var(--bg-app);
  padding: 16px; border-radius: 16px;
  border: 1px solid var(--border-dim);
}
.list-label { font-size: 11px; font-weight: 700; color: var(--txt-tertiary); text-transform: uppercase; letter-spacing: 0.05em; }

.model-list { display: flex; flex-direction: column; gap: 12px; }

.model-item-card {
  background: var(--bg-panel);
  border: 1px solid var(--border-dim);
  border-radius: 12px;
  padding: 16px;
  display: flex; flex-direction: column; gap: 12px;
  transition: all 0.2s;
}
.model-item-card:hover { border-color: var(--border-light); transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.03); }

.model-item-header { display: flex; justify-content: space-between; align-items: center; }
.model-tag { 
  font-size: 11px; font-weight: 700; color: var(--brand); 
  background: rgba(var(--brand-rgb), 0.1); padding: 4px 8px; border-radius: 6px; 
}

.icon-btn.danger {
  width: 28px; height: 28px;
  border-radius: 8px;
  color: var(--txt-tertiary);
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
  cursor: pointer;
}
.icon-btn.danger:hover { background: rgba(var(--error-rgb), 0.1); color: var(--error); }

.model-inputs { display: grid; grid-template-columns: 1.5fr 1fr 1fr; gap: 10px; }
.mini-input {
  background: var(--bg-app);
  border: 1px solid var(--border-dim);
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 12px;
  color: var(--txt-primary);
  font-family: 'JetBrains Mono';
  width: 100%;
  transition: all 0.2s;
}
.mini-input:focus { border-color: var(--brand); background: var(--bg-panel); }

.add-model-btn {
  width: 100%;
  padding: 12px;
  border: 1px dashed var(--border-dim);
  border-radius: 12px;
  background: transparent;
  color: var(--txt-secondary);
  font-size: 13px; font-weight: 600;
  display: flex; align-items: center; justify-content: center; gap: 8px;
  cursor: pointer;
  transition: all 0.2s;
}
.add-model-btn:hover { border-color: var(--brand); color: var(--brand); background: rgba(var(--brand-rgb), 0.03); }

.row-actions { display: flex; align-items: center; gap: 12px; }
.input-wrapper.small { width: 80px; position: relative; }
.unit { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); font-size: 12px; color: var(--txt-tertiary); pointer-events: none; }
.modern-input.center { text-align: center; padding-right: 24px; }

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 600px) {
  .model-inputs { grid-template-columns: 1fr; }
  .input-grid { grid-template-columns: 1fr; }
}
</style>
