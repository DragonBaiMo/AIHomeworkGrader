<script setup lang="ts">
import type { GradeConfigPayload } from "@/api/types";

const props = defineProps<{
  config: GradeConfigPayload;
}>();

const emit = defineEmits<{
  (e: "update:config", payload: Partial<GradeConfigPayload>): void;
}>();

function updateField<T extends keyof GradeConfigPayload>(key: T, value: GradeConfigPayload[T]) {
  emit("update:config", { [key]: value } as Partial<GradeConfigPayload>);
}
</script>

<template>
  <div class="settings-stage">
    <div class="settings-content animate-in">
      
      <!-- Intro -->
      <header class="page-header">
        <h2>系统参数配置</h2>
        <p>配置大语言模型 (LLM) 连接参数与全局行为。</p>
      </header>

      <div class="settings-group">
        <div class="group-label">模型连接 (LLM CONNECTION)</div>
        
        <!-- API Endpoint -->
        <div class="setting-item">
          <div class="item-meta">
            <label>API 接口地址</label>
            <span class="desc">OpenAI 兼容协议的 API Endpoint</span>
          </div>
          <div class="input-slot">
            <input
              type="text"
              class="tech-input"
              :value="config.apiUrl"
              placeholder="https://api.openai.com/v1/chat/completions"
              @input="updateField('apiUrl', ($event.target as HTMLInputElement).value)"
            />
          </div>
        </div>

        <!-- API Key -->
        <div class="setting-item">
          <div class="item-meta">
            <label>API 密钥 (Key)</label>
            <span class="desc">密钥仅存储于本地浏览器，不上传云端</span>
          </div>
          <div class="input-slot">
            <input
              type="password"
              class="tech-input"
              :value="config.apiKey"
              placeholder="sk-..."
              @input="updateField('apiKey', ($event.target as HTMLInputElement).value)"
            />
          </div>
        </div>

        <!-- Model Name -->
        <div class="setting-item">
          <div class="item-meta">
            <label>模型名称 (Model)</label>
            <span class="desc">目标调用的模型标识符</span>
          </div>
          <div class="input-slot">
            <input
              type="text"
              class="tech-input mono"
              :value="config.modelName"
              placeholder="gpt-4o"
              @input="updateField('modelName', ($event.target as HTMLInputElement).value)"
            />
          </div>
        </div>
      </div>

      <div class="settings-group">
        <div class="group-label">系统行为 (BEHAVIOR)</div>
        
        <div class="setting-item">
          <div class="item-meta">
            <label>允许非标准格式</label>
            <span class="desc">跳过 .docx 文件的严格格式校验</span>
          </div>
          <label class="toggle-switch">
            <input 
              type="checkbox" 
              :checked="config.skipFormatCheck"
              @change="updateField('skipFormatCheck', ($event.target as HTMLInputElement).checked)"
            />
            <span class="slider"></span>
          </label>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.settings-stage {
  display: flex;
  justify-content: center;
  padding-top: 20px;
}

.settings-content {
  width: 100%;
  max-width: 640px;
  display: flex;
  flex-direction: column;
  gap: 48px;
}

.page-header {
  border-bottom: 1px solid var(--border-dim);
  padding-bottom: 24px;
}
.page-header h2 { font-size: 22px; margin-bottom: 8px; color: var(--txt-primary); }
.page-header p { font-size: 14px; color: var(--txt-tertiary); }

/* Groups */
.settings-group {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.group-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.12em;
  color: var(--brand);
  opacity: 0.8;
  margin-bottom: 8px;
}

/* Items */
.setting-item {
  display: grid;
  grid-template-columns: 200px 1fr;
  align-items: center;
  gap: 24px;
}

.item-meta { display: flex; flex-direction: column; gap: 4px; }
.item-meta label { font-size: 14px; font-weight: 500; color: var(--txt-primary); }
.item-meta .desc { font-size: 12px; color: var(--txt-tertiary); }

/* Tech Input (Inset style) */
.input-slot {
  position: relative;
}
.tech-input {
  width: 100%;
  background: var(--bg-app);
  border: 1px solid var(--border-dim);
  border-radius: var(--radius-m);
  padding: 12px 16px;
  color: var(--txt-primary);
  font-size: 14px;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
  transition: all 0.2s;
}
.tech-input:focus {
  border-color: var(--brand);
  background: var(--bg-app);
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.2), 0 0 0 1px var(--brand-dim);
}
.tech-input.mono { font-family: "JetBrains Mono", monospace; letter-spacing: -0.02em; }

/* Toggle */
.toggle-switch {
  position: relative;
  width: 44px;
  height: 24px;
  justify-self: end;
}
.toggle-switch input { opacity: 0; width: 0; height: 0; }
.slider {
  position: absolute;
  cursor: pointer;
  inset: 0;
  background-color: var(--bg-active);
  border-radius: 99px;
  transition: .3s;
  border: 1px solid var(--border-light);
}
.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 2px;
  bottom: 2px;
  background-color: var(--txt-secondary);
  border-radius: 50%;
  transition: .3s var(--ease-spring);
}
input:checked + .slider { background-color: var(--brand-dim); border-color: var(--brand); }
input:checked + .slider:before { transform: translateX(20px); background-color: var(--brand); }
</style>