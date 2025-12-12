<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import type { PromptCategory, PromptConfig, PromptSection } from "@/api/types";
import { useUI } from "@/composables/useUI";

const props = defineProps<{
  config: PromptConfig | null;
  loading: boolean;
  saving: boolean;
  error: string;
}>();

const emit = defineEmits<{
  (e: "refresh"): void;
  (e: "save", payload: PromptConfig): void;
}>();

const { showToast, confirm } = useUI();
const editable = ref<PromptConfig | null>(null);
const currentKey = ref<string>("");
const collapsedModules = reactive(new Set<number>());
const expandedItems = reactive(new Set<string>()); 

const Icons = {
  Plus: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>`,
  Trash: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>`,
  Chevron: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>`,
  Refresh: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 4v6h-6"></path><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>`,
  Save: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>`,
  Code: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>`,
  Edit: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>`
};

watch(
  () => props.config,
  (val) => {
    if (!val) {
      editable.value = null;
      currentKey.value = "";
      return;
    }
    editable.value = JSON.parse(JSON.stringify(val)) as PromptConfig;
    const keys = Object.keys(val.categories);
    if (!currentKey.value || !keys.includes(currentKey.value)) {
      currentKey.value = keys[0] ?? "";
    }
    collapsedModules.clear();
    expandedItems.clear();
  },
  { deep: true, immediate: true },
);

const currentCategory = computed<PromptCategory | null>(() => {
  if (!editable.value || !currentKey.value) return null;
  return editable.value.categories[currentKey.value] ?? null;
});

function toggleModule(idx: number) {
  if (collapsedModules.has(idx)) collapsedModules.delete(idx);
  else collapsedModules.add(idx);
}

function toggleItem(mIdx: number, iIdx: number) {
  const key = `${mIdx}-${iIdx}`;
  if (expandedItems.has(key)) expandedItems.delete(key);
  else expandedItems.add(key);
}

function isItemExpanded(mIdx: number, iIdx: number) {
  return expandedItems.has(`${mIdx}-${iIdx}`);
}

function addCategory() {
  if (!editable.value) return;
  const key = `cat_${Date.now()}`;
  editable.value.categories[key] = { display_name: "新分类", sections: [] };
  currentKey.value = key;
}

function removeCategory(key: string) {
  if (!editable.value) return;
  if (Object.keys(editable.value.categories).length <= 1) {
    showToast("至少保留一个分类", "warning");
    return;
  }
  
  confirm({
    title: "删除分类",
    content: "确定要彻底删除此分类及其所有规则吗？此操作不可恢复。",
    confirmText: "确认删除",
    type: "danger",
    onConfirm: () => {
      if (!editable.value) return;
      delete editable.value.categories[key];
      if (currentKey.value === key) currentKey.value = Object.keys(editable.value.categories)[0];
      showToast("分类已删除", "success");
    }
  });
}

function addSection() {
  currentCategory.value?.sections.push({ key: "维度名称", max_score: 10, items: [] });
}
function removeSection(idx: number) { currentCategory.value?.sections.splice(idx, 1); }

function addItem(section: PromptSection, mIdx: number) {
  section.items.push({ key: "评分点", max_score: 5, description: "" });
  expandedItems.add(`${mIdx}-${section.items.length - 1}`);
}
function removeItem(section: PromptSection, idx: number) { section.items.splice(idx, 1); }

// --- Logic: Auto-calculate Score ---
function getSectionTotal(section: PromptSection) {
  return section.items.reduce((sum, item) => sum + (Number(item.max_score) || 0), 0);
}

function handleSave() {
  if (!editable.value) return;
  // Auto-calculate section scores before saving
  Object.values(editable.value.categories).forEach(cat => {
    cat.sections.forEach(sec => {
      sec.max_score = getSectionTotal(sec);
    });
  });
  emit("save", JSON.parse(JSON.stringify(editable.value)));
}
</script>

<template>
  <div class="editor-shell animate-in">
    <!-- Top Bar -->
    <header class="editor-bar">
      <div class="bar-left">
        <span class="icon" v-html="Icons.Code"></span>
        <span class="bar-title">评分规则引擎</span>
      </div>
      <div class="bar-right">
        <button class="btn ghost small icon-only" @click="emit('refresh')" title="放弃修改">
          <span v-html="Icons.Refresh"></span>
        </button>
        <button class="btn primary small" :disabled="saving || !editable" @click="handleSave">
          <span class="icon-text-desktop" v-html="Icons.Save"></span>
          <span class="btn-text">{{ saving ? "..." : "保存" }}</span>
        </button>
      </div>
    </header>

    <div v-if="error" class="error-banner">{{ error }}</div>

    <div v-if="editable" class="ide-container">
      <!-- Sidebar -->
      <aside class="sidebar-pane">
        <div class="pane-header">
          <span>分类列表</span>
          <button class="icon-btn highlight" @click="addCategory" title="新增分类">
            <span v-html="Icons.Plus"></span>
          </button>
        </div>
        <div class="file-list">
          <button
            v-for="(cat, key) in editable.categories"
            :key="key"
            class="file-item"
            :class="{ active: currentKey === key }"
            @click="currentKey = String(key)"
          >
            <span class="file-icon">#</span>
            <span class="file-name">{{ cat.display_name || key }}</span>
          </button>
        </div>
      </aside>

      <!-- Main Editor -->
      <main class="editor-pane" v-if="currentCategory">
        
        <!-- Meta Info -->
        <div class="config-header-card">
          <div class="header-row">
            <div class="field-group grow">
              <label>分类名称</label>
              <input type="text" v-model="currentCategory.display_name" class="code-input" />
            </div>
            <button class="icon-btn danger big" @click="removeCategory(currentKey)" title="删除此分类">
              <span v-html="Icons.Trash"></span>
            </button>
          </div>
          <div class="field-group">
            <label>AI 角色设定 (System Prompt)</label>
            <textarea
              v-model="editable.system_prompt"
              rows="2"
              class="code-input area"
              placeholder="设定AI的评审角色..."
            ></textarea>
          </div>
        </div>

        <!-- Rules Stack -->
        <div class="rules-stack">
          <div class="stack-label">评分维度配置</div>
          
          <TransitionGroup name="list-anim">
            <div 
              v-for="(section, sIdx) in currentCategory.sections" 
              :key="sIdx"
              class="module-block"
              :class="{ collapsed: collapsedModules.has(sIdx) }"
            >
              <!-- Module Header -->
              <header class="module-head" @click="toggleModule(sIdx)">
                <div class="head-left">
                  <div class="chevron-box" :class="{ rotate: !collapsedModules.has(sIdx) }">
                    <span v-html="Icons.Chevron"></span>
                  </div>
                  <input type="text" class="transparent-input title" v-model="section.key" placeholder="维度名称" @click.stop />
                </div>
                <div class="head-right" @click.stop>
                  <span class="tag mobile-hide">总分</span>
                  <!-- Read-only computed score -->
                  <div class="score-badge">{{ getSectionTotal(section) }}</div>
                  <span class="divider"></span>
                  <button class="icon-btn danger" @click="removeSection(sIdx)" title="删除维度">
                    <span v-html="Icons.Trash"></span>
                  </button>
                </div>
              </header>

              <!-- Items Container -->
              <div v-show="!collapsedModules.has(sIdx)" class="items-wrapper">
                <div class="items-grid">
                  <div v-for="(item, iIdx) in section.items" :key="iIdx" class="item-card">
                    
                    <!-- Item Header: Key & Score -->
                    <div class="item-head" @click="toggleItem(sIdx, iIdx)">
                      <div class="item-head-left">
                        <div class="tiny-chevron" :class="{ open: isItemExpanded(sIdx, iIdx) }">
                          <span v-html="Icons.Chevron"></span>
                        </div>
                        <input type="text" v-model="item.key" class="item-key-input" placeholder="评分源 (如: 逻辑性)" @click.stop />
                      </div>
                      
                      <div class="item-head-right" @click.stop>
                         <span class="item-tag">分值</span>
                         <input type="number" v-model.number="item.max_score" class="item-score-input" />
                         <button class="icon-btn danger small" @click="removeItem(section, iIdx)">
                           <span v-html="Icons.Trash"></span>
                         </button>
                      </div>
                    </div>

                    <!-- Item Body: Description (Collapsible) -->
                    <div v-show="isItemExpanded(sIdx, iIdx)" class="item-body">
                      <textarea 
                        v-model="item.description" 
                        class="desc-textarea" 
                        placeholder="在此输入详细的评分标准描述..."
                        rows="3"
                      ></textarea>
                    </div>

                  </div>

                  <button class="add-item-btn" @click="addItem(section, sIdx)">
                    <span class="icon-box" v-html="Icons.Plus"></span> 添加评分细则
                  </button>
                </div>
              </div>
            </div>
          </TransitionGroup>

          <button class="new-module-btn" @click="addSection">
            <span v-html="Icons.Plus"></span> 新增评分维度
          </button>
        </div>

      </main>
    </div>
  </div>
</template>

<style scoped>
.editor-shell {
  display: flex; flex-direction: column; height: 100%; background: var(--bg-app);
}

.editor-bar {
  height: 48px; border-bottom: 1px solid var(--border-dim);
  display: flex; justify-content: space-between; align-items: center;
  padding: 0 24px; background: var(--bg-panel);
}
.bar-left { display: flex; align-items: center; gap: 8px; color: var(--brand); }
.bar-title { font-weight: 600; font-size: 14px; color: var(--txt-primary); }
.bar-right { display: flex; gap: 12px; }

/* Icons & Buttons */
.icon-btn {
  background: transparent; border: none; color: var(--txt-tertiary);
  cursor: pointer; padding: 6px; border-radius: 4px;
  display: flex; align-items: center; justify-content: center; transition: all 0.2s;
}
.icon-btn:hover { color: var(--txt-primary); background: var(--bg-active); }
.icon-btn.highlight:hover { color: var(--brand); background: var(--brand-dim); }
.icon-btn.danger:hover { color: var(--error); background: var(--error-bg); }
.icon-btn.big { padding: 8px; }
.btn.icon-only { width: 32px; padding: 0; }
.btn-text { margin-left: 4px; }
.icon-text-desktop { display: inline-flex; }

/* Layout */
.ide-container { display: flex; flex: 1; overflow: hidden; }

.sidebar-pane {
  width: 240px; background: var(--bg-panel);
  border-right: 1px solid var(--border-dim);
  display: flex; flex-direction: column; flex-shrink: 0;
}
@media (max-width: 768px) {
  .ide-container { flex-direction: column; }
  .sidebar-pane { width: 100%; height: auto; max-height: 120px; border-right: none; border-bottom: 1px solid var(--border-dim); }
  .file-list { flex-direction: row; overflow-x: auto; padding-bottom: 8px; }
  .file-item { white-space: nowrap; }
  .editor-bar { padding: 0 16px; }
  .icon-text-desktop { display: none; }
  .btn-text { margin-left: 0; }
}

.pane-header {
  padding: 16px; font-size: 12px; font-weight: 600; color: var(--txt-tertiary);
  display: flex; justify-content: space-between; align-items: center;
}
.file-list { display: flex; flex-direction: column; padding: 0 8px; gap: 2px; }
.file-item {
  display: flex; align-items: center; gap: 8px; padding: 8px 12px;
  background: transparent; border: none; border-radius: 4px; cursor: pointer;
  color: var(--txt-secondary); font-family: "JetBrains Mono", monospace; font-size: 13px; text-align: left;
}
.file-item:hover { background: var(--bg-active); color: var(--txt-primary); }
.file-item.active { background: var(--bg-active); color: var(--brand); }
.file-icon { opacity: 0.5; }

.editor-pane {
  flex: 1; overflow-y: auto; padding: 32px 40px;
  display: flex; flex-direction: column; gap: 32px;
}
@media (max-width: 768px) { .editor-pane { padding: 20px 16px; gap: 24px; } }

/* Config Header */
.config-header-card {
  display: flex; flex-direction: column; gap: 16px;
  padding-bottom: 32px; border-bottom: 1px dashed var(--border-dim);
}
.header-row { display: flex; gap: 16px; align-items: flex-end; }
.grow { flex: 1; }
.field-group label {
  display: block; font-size: 12px; color: var(--txt-tertiary); margin-bottom: 8px; font-weight: 500;
}
.code-input {
  width: 100%; background: var(--bg-card); border: 1px solid var(--border-dim);
  color: var(--txt-primary); padding: 10px; font-family: "JetBrains Mono", monospace;
  font-size: 13px; border-radius: var(--radius-s);
}
.code-input:focus { border-color: var(--brand); outline: none; }
.code-input.area { min-height: 80px; line-height: 1.6; }

/* Rules Stack */
.rules-stack { display: flex; flex-direction: column; gap: 16px; }
.stack-label { font-size: 12px; font-weight: 600; color: var(--txt-tertiary); margin-bottom: 8px; }

/* Module Block */
.module-block {
  border: 1px solid var(--border-dim); border-radius: var(--radius-m);
  background: var(--bg-panel); overflow: hidden;
  transition: all 0.3s var(--ease-out);
}
.module-block.collapsed { border-color: transparent; background: var(--bg-panel); }

.module-head {
  display: flex; justify-content: space-between; 
  padding: 12px 24px; /* 增加头部内边距 */
  background: var(--bg-panel); border-bottom: 1px solid var(--border-dim);
  align-items: center; cursor: pointer; user-select: none; transition: background 0.2s;
}
.module-head:hover { background: var(--bg-active); }
.module-block.collapsed .module-head { border-bottom-color: transparent; }

.head-left { display: flex; align-items: center; gap: 24px; } /* 箭头与标题拉开距离 */
.head-right { display: flex; align-items: center; gap: 12px; }
.chevron-box {
  color: var(--txt-tertiary); display: flex; align-items: center;
  transition: transform 0.3s var(--ease-spring);
}
.chevron-box.rotate { transform: rotate(90deg); }

.transparent-input {
  background: transparent; border: none; color: var(--txt-primary);
  font-family: inherit; font-size: 14px;
}
.transparent-input.title { 
  font-weight: 600; width: 220px; cursor: text; 
  padding-left: 8px; /* 文字自身再向右微调 */
}
/* Read-only Score Badge */
.score-badge {
  font-family: "JetBrains Mono"; font-weight: 600; font-size: 13px;
  /* 冷淡的仪表盘风格，区分于可编辑的 Input */
  color: var(--txt-secondary); 
  background: var(--bg-active);
  border: 1px solid var(--border-dim);
  padding: 4px 12px; 
  border-radius: 99px; /* 胶囊形，与方形输入框区分 */
  min-width: 48px; text-align: center;
  cursor: default; user-select: none;
}
.tag { font-size: 12px; color: var(--txt-tertiary); }
.divider { width: 1px; height: 16px; background: var(--border-dim); margin: 0 4px; }

@media (max-width: 600px) {
  .transparent-input.title { width: 140px; text-overflow: ellipsis; }
  .mobile-hide { display: none; }
  .head-left, .head-right { gap: 8px; }
  .module-head { padding: 10px 12px; }
}

/* --- New Item Card Style --- */
.items-wrapper {
  background: var(--bg-card); 
  padding: 20px; /* 增加内边距，让卡片不要贴边 */
}
.items-grid {
  display: flex; flex-direction: column; gap: 12px; /* 拉大卡片间距 */
}

.item-card {
  background: var(--bg-panel); 
  border: 1px solid var(--border-dim);
  border-radius: 10px; /* 更圆润 */
  overflow: hidden;
  transition: all 0.2s var(--ease-out);
  box-shadow: 0 1px 2px rgba(0,0,0,0.05); /* 微弱投影 */
}
.item-card:hover { 
  border-color: var(--border-light); 
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

/* Item Header */
.item-head {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 28px; /* 保持外围舒适的大边距 */
  cursor: pointer; user-select: none;
  background: var(--bg-panel);
}
.item-head-left { display: flex; align-items: center; gap: 32px; } /* 暴力拉开间距：32px */
.item-head-right { display: flex; align-items: center; gap: 12px; }

.tiny-chevron {
  width: 20px; height: 20px; display: flex; align-items: center; justify-content: center;
  color: var(--txt-tertiary); transition: transform 0.3s var(--ease-spring);
  border-radius: 4px;
}
.tiny-chevron:hover { background: var(--bg-active); color: var(--txt-primary); }
.tiny-chevron.open { transform: rotate(90deg); color: var(--brand); }

.item-key-input {
  background: transparent; border: 1px solid transparent; 
  color: var(--error); 
  font-family: "JetBrains Mono"; font-size: 14px; font-weight: 600;
  width: 220px; /* 稍微加宽 */
  padding: 6px 12px; /* 增加内部左边距，文字再次右移 */
  border-radius: 6px;
  transition: all 0.2s;
}
.item-key-input:hover { background: var(--bg-hover); }
.item-key-input:focus { outline: none; background: var(--bg-active); border-color: var(--border-dim); }

.item-score-input {
  width: 42px; background: var(--bg-app); border: 1px solid var(--border-dim);
  border-radius: 6px; text-align: center; color: var(--brand);
  font-family: "JetBrains Mono"; font-size: 13px; padding: 4px 0; font-weight: 600;
}
.item-score-input:focus { border-color: var(--brand); outline: none; box-shadow: 0 0 0 2px var(--brand-dim); }

.item-tag { 
  font-size: 11px; font-weight: 600; color: var(--txt-tertiary); 
  text-transform: uppercase; letter-spacing: 0.05em;
}

/* Item Body (Drawer) */
.item-body {
  border-top: 1px solid var(--border-dim);
  background: var(--bg-app); /* 比卡片深一点，形成凹槽感 */
  position: relative;
}
/* 装饰性左侧线条，增强层级感 */
.item-body::before {
  content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
  background: var(--brand); opacity: 0.5;
}

.desc-textarea {
  width: 100%; border: none; background: transparent; 
  padding: 16px 20px; /* 舒适的内边距 */
  color: var(--txt-secondary); /* 稍微柔和一点的文字颜色 */
  font-family: "JetBrains Mono"; font-size: 13px;
  resize: vertical; min-height: 80px; line-height: 1.6; display: block;
}
.desc-textarea:focus { outline: none; color: var(--txt-primary); background: rgba(255,255,255,0.02); }
.desc-textarea::placeholder { color: var(--txt-dim); font-style: italic; }

/* Mobile Adjustments for Item Card */
@media (max-width: 600px) {
  .items-wrapper { padding: 12px; }
  .item-head { padding: 12px; }
  .item-key-input { width: 140px; font-size: 13px; }
  .item-tag { display: none; }
}

.add-item-btn {
  margin-top: 12px; align-self: center; /* 居中按钮更优雅 */
  background: transparent; border: 1px dashed var(--border-dim);
  color: var(--txt-tertiary); padding: 8px 24px; border-radius: 99px; /* 胶囊型 */
  cursor: pointer; display: flex; align-items: center; gap: 8px; font-size: 12px;
  transition: all 0.2s;
}
.add-item-btn:hover { 
  color: var(--brand); border-color: var(--brand); 
  background: var(--brand-dim);
}

.new-module-btn {
  width: 100%; padding: 12px; border: 1px dashed var(--border-dim);
  background: transparent; color: var(--txt-tertiary); cursor: pointer;
  border-radius: var(--radius-m); display: flex; align-items: center; justify-content: center;
  gap: 8px; font-size: 13px;
}
.new-module-btn:hover { border-color: var(--txt-secondary); color: var(--txt-primary); background: var(--bg-active); }

/* Transitions */
.list-anim-move, .list-anim-enter-active, .list-anim-leave-active { transition: all 0.3s var(--ease-spring); }
.list-anim-enter-from, .list-anim-leave-to { opacity: 0; transform: scale(0.98); }
</style>