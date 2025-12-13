<script setup lang="ts">
import type { GradeConfigPayload, PromptSettings } from "@/api/types";
import { useSettingsPanel } from "../logic/useSettingsPanel";

const props = defineProps<{
  config: GradeConfigPayload;
  promptSettings: PromptSettings;
}>();

const emit = defineEmits<{
  (e: "update:config", payload: Partial<GradeConfigPayload>): void;
  (e: "update:promptSettings", payload: Partial<PromptSettings>): void;
  (e: "submit"): void;
}>();

const {
  Icons,
  localConfig,
  handleChange,
  handleToggleMulti,
  handleModelChange,
  addModelRow,
  removeModelRow,
  handlePromptSetting,
} = useSettingsPanel(props, emit);
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
 
 <style scoped src="../styles/settings-panel.css"></style>
