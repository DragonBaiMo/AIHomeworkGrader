<script setup lang="ts">
import { ref } from "vue";
import type { GradeConfigPayload } from "@/api/types";

const props = defineProps<{
  config: GradeConfigPayload;
}>();

const emit = defineEmits<{
  (e: "update:config", payload: Partial<GradeConfigPayload>): void;
  (e: "submit"): void;
}>();

const localConfig = ref({ ...props.config });

const Icons = {
  Server: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect><rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect><line x1="6" y1="6" x2="6.01" y2="6"></line><line x1="6" y1="18" x2="6.01" y2="18"></line></svg>`,
  Key: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"></path></svg>`,
  Cpu: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line><line x1="20" y1="9" x2="23" y2="9"></line><line x1="20" y1="14" x2="23" y2="14"></line><line x1="1" y1="9" x2="4" y2="9"></line><line x1="1" y1="14" x2="4" y2="14"></line></svg>`,
  Check: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`
};

function handleChange<T extends keyof GradeConfigPayload>(key: T, value: GradeConfigPayload[T]) {
  localConfig.value[key] = value;
  emit("update:config", { [key]: value });
}
</script>

<template>
  <div class="settings-layout animate-in">
    <div class="settings-card glass-morphism">
      <header class="card-header">
        <div class="header-main">
          <div class="icon-badge">
            <span v-html="Icons.Server"></span>
          </div>
          <div class="header-text">
            <h2 class="card-title">系统连接</h2>
            <p class="card-desc">LLM Service Configuration</p>
          </div>
        </div>
        <button class="action-btn primary" @click="emit('submit')">
          <span v-html="Icons.Check"></span>
          <span>保存配置</span>
        </button>
      </header>

      <div class="card-body">
        
        <div class="input-section">
          <div class="input-group">
            <label class="field-label">API 端点 <span class="sub">(Base URL)</span></label>
            <div class="input-wrapper">
              <input 
                type="text" 
                class="modern-input font-mono" 
                :value="localConfig.apiUrl"
                @input="handleChange('apiUrl', ($event.target as HTMLInputElement).value)"
                placeholder="https://api.openai.com/v1"
              />
              <div class="focus-ring"></div>
            </div>
          </div>

          <div class="input-group">
            <label class="field-label">API 密钥 <span class="sub">(Secret Key)</span></label>
            <div class="input-wrapper">
              <input 
                type="password" 
                class="modern-input font-mono" 
                :value="localConfig.apiKey"
                @input="handleChange('apiKey', ($event.target as HTMLInputElement).value)"
                placeholder="sk-..."
              />
              <div class="focus-ring"></div>
            </div>
          </div>

          <div class="input-group">
            <label class="field-label">模型名称 <span class="sub">(Model Name)</span></label>
            <div class="input-wrapper">
              <input 
                type="text" 
                class="modern-input font-mono" 
                :value="localConfig.modelName"
                @input="handleChange('modelName', ($event.target as HTMLInputElement).value)"
                placeholder="gpt-4o"
              />
              <div class="focus-ring"></div>
            </div>
          </div>
        </div>

        <div class="divider-line"></div>

        <div class="toggle-section">
          <div class="toggle-info">
            <span class="toggle-title">模拟运行模式 (Mock Mode)</span>
            <span class="toggle-desc">跳过真实 API 调用，使用本地随机数据生成结果</span>
          </div>
          <label class="ios-switch">
            <input 
              type="checkbox" 
              :checked="localConfig.mock"
              @change="handleChange('mock', ($event.target as HTMLInputElement).checked)"
            />
            <div class="switch-body">
              <div class="switch-knob"></div>
            </div>
          </label>
        </div>

      </div>
    </div>
  </div>
</template>

<style scoped>
.settings-layout {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding-top: 80px;
  height: 100%;
  width: 100%;
}

.settings-card {
  width: 100%;
  max-width: 500px;
  border-radius: var(--radius-xl);
  background: var(--bg-panel);
  border: 1px solid var(--border-dim);
  box-shadow: var(--shadow-float);
  overflow: hidden;
  position: relative;
  transition: transform 0.3s var(--ease-out);
}
.settings-card:hover { transform: translateY(-2px); }

/* Top highlight line */
.settings-card::before {
  content: ""; position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
}

.card-header {
  padding: 24px 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-dim);
  background: var(--bg-panel);
}

.header-main { display: flex; align-items: center; gap: 16px; }
.icon-badge {
  width: 40px; height: 40px;
  border-radius: 10px;
  background: var(--bg-active);
  color: var(--txt-primary);
  display: flex; align-items: center; justify-content: center;
  border: 1px solid var(--border-dim);
}

.header-text { display: flex; flex-direction: column; gap: 2px; }
.card-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--txt-primary);
  letter-spacing: -0.01em;
}
.card-desc {
  font-size: 12px;
  color: var(--txt-tertiary);
  font-family: 'JetBrains Mono';
}

.action-btn {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px; font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s;
}
.action-btn.primary { background: var(--brand); color: #fff; box-shadow: 0 4px 12px rgba(var(--brand-rgb), 0.25); }
.action-btn.primary:hover { transform: translateY(-1px); box-shadow: 0 8px 20px rgba(var(--brand-rgb), 0.35); }

.card-body {
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 32px;
  background: var(--bg-app); /* Deepen the body background */
}

/* Inputs */
.input-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-label {
  font-size: 12px; font-weight: 600; color: var(--txt-secondary);
}
.field-label .sub { color: var(--txt-tertiary); font-weight: 400; font-size: 11px; }

.input-wrapper { position: relative; width: 100%; }

.modern-input {
  width: 100%;
  padding: 10px 12px;
  background: var(--bg-panel);
  border: 1px solid var(--border-dim);
  border-radius: 8px;
  color: var(--txt-primary);
  font-size: 14px;
  transition: all 0.2s;
}
.modern-input.font-mono { font-family: 'JetBrains Mono', monospace; font-size: 13px; }
.modern-input:focus { outline: none; border-color: var(--brand); }

.focus-ring {
  position: absolute; inset: 0; pointer-events: none;
  border-radius: 8px;
  box-shadow: 0 0 0 3px var(--brand-dim);
  opacity: 0; transition: opacity 0.2s;
}
.modern-input:focus + .focus-ring { opacity: 1; }

/* Divider */
.divider-line {
  height: 1px; background: var(--border-dim);
  width: 100%;
}

/* Toggle */
.toggle-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
}
.toggle-info { display: flex; flex-direction: column; gap: 4px; }
.toggle-title { font-size: 14px; font-weight: 600; color: var(--txt-primary); }
.toggle-desc { font-size: 12px; color: var(--txt-tertiary); }

/* iOS Switch Reuse */
.ios-switch { position: relative; width: 44px; height: 24px; cursor: pointer; }
.ios-switch input { display: none; }
.switch-body {
  position: absolute; inset: 0;
  background: var(--bg-active);
  border-radius: 99px;
  border: 1px solid var(--border-dim);
  transition: all 0.3s;
}
.switch-knob {
  position: absolute; top: 2px; left: 2px;
  width: 18px; height: 18px;
  background: #fff;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.ios-switch input:checked + .switch-body { background: var(--brand); border-color: var(--brand); }
.ios-switch input:checked + .switch-body .switch-knob { transform: translateX(20px); }

@media (max-width: 600px) {
  .settings-layout { padding-top: 20px; padding-left: 16px; padding-right: 16px; }
  .settings-card { height: auto; }
}
</style>