<script setup lang="ts">
import { ref } from "vue";
import type { GradeConfigPayload } from "@/api/types";

const props = defineProps<{
  config: GradeConfigPayload;
}>();

const emit = defineEmits<{
  (e: "update:config", payload: Partial<GradeConfigPayload>): void;
  (e: "submit"): void; // Return to workspace
}>();

const localConfig = ref({ ...props.config });

function handleChange<T extends keyof GradeConfigPayload>(key: T, value: GradeConfigPayload[T]) {
  localConfig.value[key] = value;
  emit("update:config", { [key]: value });
}
</script>

<template>
  <div class="settings-layout animate-in">
    <div class="settings-card glass">
      <header class="settings-header">
        <h2 class="title">系统设置</h2>
        <p class="subtitle">配置 API 连接与模型参数</p>
      </header>

      <div class="settings-body">
        <div class="form-group">
          <label class="form-label">API Base URL</label>
          <input 
            type="text" 
            class="form-input" 
            :value="localConfig.apiUrl"
            @input="handleChange('apiUrl', ($event.target as HTMLInputElement).value)"
            placeholder="https://api.openai.com/v1"
          />
          <p class="form-hint">LLM 服务端点地址</p>
        </div>

        <div class="form-group">
          <label class="form-label">API Key</label>
          <input 
            type="password" 
            class="form-input" 
            :value="localConfig.apiKey"
            @input="handleChange('apiKey', ($event.target as HTMLInputElement).value)"
            placeholder="sk-..."
          />
        </div>

        <div class="form-group">
          <label class="form-label">Model Name</label>
          <input 
            type="text" 
            class="form-input" 
            :value="localConfig.modelName"
            @input="handleChange('modelName', ($event.target as HTMLInputElement).value)"
            placeholder="gpt-4o"
          />
        </div>

        <div class="divider"></div>

        <div class="form-group row">
          <div class="text-col">
            <label class="form-label">模拟模式 (Mock)</label>
            <p class="form-hint">不调用真实 API，仅返回测试数据</p>
          </div>
          <label class="toggle">
            <input 
              type="checkbox" 
              :checked="localConfig.mock"
              @change="handleChange('mock', ($event.target as HTMLInputElement).checked)"
            />
            <span class="track"></span>
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
  padding-top: 40px;
}

.settings-card {
  width: 100%;
  max-width: 500px;
  border-radius: var(--radius-l);
  padding: 40px;
  background: var(--bg-card);
  box-shadow: var(--shadow-float);
}

.settings-header { margin-bottom: 32px; text-align: center; }
.title { font-size: 24px; font-weight: 700; margin-bottom: 8px; color: var(--txt-primary); }
.subtitle { color: var(--txt-tertiary); font-size: 14px; }

.settings-body { display: flex; flex-direction: column; gap: 24px; }

.form-group { display: flex; flex-direction: column; gap: 8px; }
.form-group.row { flex-direction: row; justify-content: space-between; align-items: center; }

.form-label { font-size: 13px; font-weight: 600; color: var(--txt-secondary); }
.form-input {
  width: 100%;
  height: 44px;
  padding: 0 16px;
  background: var(--bg-panel);
  border: 1px solid var(--border-dim);
  border-radius: 8px;
  color: var(--txt-primary);
  font-family: "JetBrains Mono";
  font-size: 14px;
  transition: all 0.2s;
}
.form-input:focus {
  border-color: var(--brand);
  box-shadow: 0 0 0 3px var(--brand-dim);
  background: var(--bg-app);
}
.form-hint { font-size: 12px; color: var(--txt-tertiary); }

.divider { height: 1px; background: var(--border-dim); margin: 8px 0; }

/* Toggle */
.toggle { position: relative; width: 44px; height: 24px; cursor: pointer; }
.toggle input { display: none; }
.track {
  position: absolute; inset: 0; background: var(--bg-active);
  border-radius: 99px; transition: all 0.3s;
  border: 1px solid var(--border-dim);
}
.track::after {
  content: ''; position: absolute; top: 2px; left: 2px;
  width: 18px; height: 18px; background: var(--txt-secondary);
  border-radius: 50%; transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}
input:checked + .track { background: var(--brand); border-color: var(--brand); }
input:checked + .track::after { transform: translateX(20px); background: #fff; }

@media (max-width: 600px) {
  .settings-card { padding: 24px; }
}
</style>