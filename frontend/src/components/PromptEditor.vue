<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import type { PromptCategory, PromptConfig, PromptSection } from "@/api/types";
import { useUI } from "@/composables/useUI";
import { fetchPromptPreview } from "@/api/client";

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
const previewOpen = ref(false);
const previewLoading = ref(false);
const previewError = ref("");
const previewScoreTargetMax = ref<number>(60);
const previewSystemPrompt = ref("");
const previewUserPrompt = ref("");
const previewRubricMax = ref<number | null>(null);

const Icons = {
  Plus: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>`,
  Trash: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>`,
  ChevronRight: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"></polyline></svg>`,
  Refresh: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 4v6h-6"></path><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>`,
  Save: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>`,
  Eye: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>`,
  Folder: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>`,
  FileCode: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>`
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
    title: "确认删除",
    content: "确定要彻底删除此分类及其所有规则吗？",
    confirmText: "删除",
    type: "danger",
    onConfirm: () => {
      if (!editable.value) return;
      delete editable.value.categories[key];
      if (currentKey.value === key) currentKey.value = Object.keys(editable.value.categories)[0];
    }
  });
}

function addSection() {
  currentCategory.value?.sections.push({ key: "新维度", max_score: 10, items: [] });
}
function removeSection(idx: number) { currentCategory.value?.sections.splice(idx, 1); }

function addItem(section: PromptSection, mIdx: number) {
  section.items.push({ key: "评分点", max_score: 5, description: "" });
  expandedItems.add(`${mIdx}-${section.items.length - 1}`);
}
function removeItem(section: PromptSection, idx: number) { section.items.splice(idx, 1); }

function getSectionTotal(section: PromptSection) {
  return section.items.reduce((sum, item) => sum + (Number(item.max_score) || 0), 0);
}

function handleSave() {
  if (!editable.value) return;
  Object.values(editable.value.categories).forEach(cat => {
    cat.sections.forEach(sec => sec.max_score = getSectionTotal(sec));
  });
  emit("save", JSON.parse(JSON.stringify(editable.value)));
}

async function refreshPreview() {
  if (!editable.value || !currentKey.value) return;
  previewLoading.value = true;
  previewError.value = "";
  try {
    const resp = await fetchPromptPreview(editable.value, currentKey.value, previewScoreTargetMax.value);
    previewSystemPrompt.value = resp.system_prompt || "";
    previewUserPrompt.value = resp.user_prompt || "";
    previewRubricMax.value = typeof resp.score_rubric_max === "number" ? resp.score_rubric_max : null;
  } catch (err) {
    previewError.value = (err as Error).message;
  } finally {
    previewLoading.value = false;
  }
}
</script>

<template>
  <div class="ide-layout animate-in">
    <!-- Toolbar -->
    <header class="ide-toolbar glass">
      <div class="toolbar-left">
        <span class="icon-box" v-html="Icons.FileCode"></span>
        <span class="toolbar-title">规则编辑器</span>
      </div>
      <div class="toolbar-right">
        <button class="btn ghost small icon-only" @click="emit('refresh')" title="重置">
          <span v-html="Icons.Refresh"></span>
        </button>
        <button class="btn ghost small" :class="{ active: previewOpen }" @click="previewOpen = !previewOpen; if(previewOpen) refreshPreview();">
          <span v-html="Icons.Eye"></span> 预览
        </button>
        <button class="btn primary small" :disabled="saving || !editable" @click="handleSave">
          <span v-html="Icons.Save"></span> {{ saving ? "保存中..." : "保存" }}
        </button>
      </div>
    </header>

    <div class="ide-body" v-if="editable">
      <!-- Sidebar -->
      <aside class="ide-sidebar glass">
        <div class="sidebar-header">
          <span class="sidebar-title">分类 (Categories)</span>
          <button class="icon-btn tiny" @click="addCategory"><span v-html="Icons.Plus"></span></button>
        </div>
        <div class="file-tree">
          <button
            v-for="(cat, key) in editable.categories"
            :key="key"
            class="tree-item"
            :class="{ active: currentKey === key }"
            @click="currentKey = String(key)"
          >
            <span class="tree-icon" v-html="Icons.Folder"></span>
            <span class="tree-label">{{ cat.display_name || key }}</span>
          </button>
        </div>
      </aside>

      <!-- Editor -->
      <main class="ide-surface" v-if="currentCategory">
        
        <div class="config-panel">
          <div class="panel-row">
            <div class="input-group grow">
              <label>分类名称</label>
              <input type="text" v-model="currentCategory.display_name" class="ide-input" />
            </div>
            <button class="btn danger small icon-only" @click="removeCategory(currentKey)">
              <span v-html="Icons.Trash"></span>
            </button>
          </div>
          <div class="input-group">
            <label>AI 角色设定 (System Prompt)</label>
            <textarea
              v-model="editable.system_prompt"
              rows="3"
              class="ide-input area"
              placeholder="你是一位严格的计算机科学教授..."
            ></textarea>
          </div>
        </div>

        <div class="rules-canvas">
          <div class="canvas-header">
            <span class="canvas-title">评分维度 (Rubric)</span>
            <button class="btn ghost small" @click="addSection"><span v-html="Icons.Plus"></span> 新增维度</button>
          </div>

          <div class="blocks-container">
            <TransitionGroup name="list-anim">
              <div 
                v-for="(section, sIdx) in currentCategory.sections" 
                :key="sIdx"
                class="rule-block"
                :class="{ collapsed: collapsedModules.has(sIdx) }"
              >
                <div class="block-header" @click="toggleModule(sIdx)">
                  <div class="header-left">
                    <span class="chevron" :class="{ rot: !collapsedModules.has(sIdx) }" v-html="Icons.ChevronRight"></span>
                    <input type="text" v-model="section.key" class="invisible-input title" placeholder="维度名称" @click.stop />
                  </div>
                  <div class="header-right">
                    <span class="badge score">{{ getSectionTotal(section) }} pts</span>
                    <button class="icon-btn tiny danger" @click.stop="removeSection(sIdx)"><span v-html="Icons.Trash"></span></button>
                  </div>
                </div>

                <div class="block-body" v-show="!collapsedModules.has(sIdx)">
                  <div class="sub-items">
                    <div v-for="(item, iIdx) in section.items" :key="iIdx" class="sub-item">
                      <div class="item-row">
                        <div class="item-left" @click="toggleItem(sIdx, iIdx)">
                          <span class="chevron tiny" :class="{ rot: isItemExpanded(sIdx, iIdx) }" v-html="Icons.ChevronRight"></span>
                          <input type="text" v-model="item.key" class="invisible-input" placeholder="评分细则" @click.stop />
                        </div>
                        <div class="item-right">
                          <input type="number" v-model.number="item.max_score" class="score-input" />
                          <button class="icon-btn tiny danger" @click="removeItem(section, iIdx)"><span v-html="Icons.Trash"></span></button>
                        </div>
                      </div>
                      
                      <div class="item-desc" v-show="isItemExpanded(sIdx, iIdx)">
                        <textarea 
                          v-model="item.description" 
                          class="ide-input transparent" 
                          placeholder="描述评分标准..."
                        ></textarea>
                      </div>
                    </div>
                  </div>
                  
                  <button class="add-sub-btn" @click="addItem(section, sIdx)">
                    <span v-html="Icons.Plus"></span> 添加细则
                  </button>
                </div>
              </div>
            </TransitionGroup>
          </div>
        </div>
      </main>

      <!-- Preview -->
      <aside v-if="previewOpen" class="ide-preview glass">
        <div class="preview-header">
          <span class="preview-title">实时预览</span>
          <button class="icon-btn tiny" @click="refreshPreview"><span v-html="Icons.Refresh"></span></button>
        </div>
        
        <div class="preview-content">
          <div class="preview-meta">
             <div class="meta-item">
               <label>目标满分</label>
               <input type="number" v-model.number="previewScoreTargetMax" class="ide-input small" @change="refreshPreview" />
             </div>
             <div class="meta-item">
               <label>规则总分</label>
               <span class="value">{{ previewRubricMax ?? "-" }}</span>
             </div>
          </div>
          
          <div class="code-block">
            <div class="code-label">System Prompt</div>
            <pre class="code-content">{{ previewSystemPrompt }}</pre>
          </div>
           <div class="code-block">
            <div class="code-label">User Prompt</div>
            <pre class="code-content">{{ previewUserPrompt }}</pre>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
/* --- IDE Layout --- */
.ide-layout {
  display: flex;
  flex-direction: column;
  height: 100%;
  border-radius: var(--radius-l);
  overflow: hidden;
  background: var(--bg-app);
  border: 1px solid var(--border-dim);
}

/* Toolbar */
.ide-toolbar {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  border-bottom: 1px solid var(--border-dim);
  z-index: 20;
}
.toolbar-left { display: flex; align-items: center; gap: 10px; color: var(--txt-primary); }
.toolbar-title { font-weight: 600; font-size: 14px; }
.toolbar-right { display: flex; gap: 10px; }

/* Body Split */
.ide-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* Sidebar */
.ide-sidebar {
  width: 240px;
  border-right: 1px solid var(--border-dim);
  display: flex;
  flex-direction: column;
  background: var(--bg-panel);
}
.sidebar-header {
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  font-size: 11px;
  font-weight: 600;
  color: var(--txt-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--border-dim);
}

.file-tree { padding: 8px; display: flex; flex-direction: column; gap: 2px; }
.tree-item {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 8px;
  border-radius: 4px;
  border: none; background: transparent;
  color: var(--txt-secondary);
  font-size: 13px;
  cursor: pointer;
  width: 100%; text-align: left;
}
.tree-item:hover { background: var(--bg-hover); color: var(--txt-primary); }
.tree-item.active { background: var(--bg-active); color: var(--brand); }
.tree-icon { color: var(--txt-tertiary); display: flex; }
.tree-item.active .tree-icon { color: var(--brand); }

/* Main Surface */
.ide-surface {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  background: var(--bg-app);
  padding: 32px;
  gap: 32px;
}

/* Config Panel */
.config-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-bottom: 24px;
  border-bottom: 1px dashed var(--border-dim);
}
.panel-row { display: flex; gap: 16px; align-items: flex-end; }
.grow { flex: 1; }

.input-group label {
  display: block; font-size: 11px; font-weight: 600; 
  color: var(--txt-tertiary); margin-bottom: 6px;
}
.ide-input {
  width: 100%;
  background: var(--bg-panel);
  border: 1px solid var(--border-dim);
  color: var(--txt-primary);
  padding: 8px 12px;
  font-family: "JetBrains Mono", monospace;
  font-size: 13px;
  border-radius: 6px;
  transition: all 0.2s;
}
.ide-input:focus { border-color: var(--brand); box-shadow: 0 0 0 2px var(--brand-dim); }
.ide-input.area { line-height: 1.6; }
.ide-input.transparent { background: transparent; border-color: transparent; padding: 0; }
.ide-input.transparent:focus { background: var(--bg-panel); border-color: var(--border-dim); padding: 8px; }

/* Rules Canvas */
.rules-canvas { display: flex; flex-direction: column; gap: 16px; }
.canvas-header {
  display: flex; justify-content: space-between; align-items: center;
}
.canvas-title { font-size: 14px; font-weight: 700; color: var(--txt-secondary); }

.rule-block {
  background: var(--bg-panel);
  border: 1px solid var(--border-dim);
  border-radius: 8px;
  margin-bottom: 12px;
  overflow: hidden;
}
.rule-block.collapsed { background: var(--bg-app); }

.block-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 16px;
  cursor: pointer;
  background: var(--bg-active);
  border-bottom: 1px solid var(--border-dim);
}
.rule-block.collapsed .block-header { border-bottom: none; background: transparent; }

.header-left, .header-right { display: flex; align-items: center; gap: 12px; }

.invisible-input {
  background: transparent; border: 1px solid transparent;
  color: var(--txt-primary); font-family: inherit; font-size: 13px;
  padding: 4px; border-radius: 4px;
}
.invisible-input:hover { background: var(--bg-hover); }
.invisible-input:focus { background: var(--bg-app); border-color: var(--brand); }
.invisible-input.title { font-weight: 600; width: 200px; }

.badge.score {
  font-family: "JetBrains Mono"; font-size: 11px;
  background: var(--bg-app); border: 1px solid var(--border-dim);
  padding: 2px 8px; border-radius: 99px; color: var(--txt-secondary);
}

.block-body { padding: 16px; background: var(--bg-panel); }
.sub-items { display: flex; flex-direction: column; gap: 8px; }

.sub-item {
  border: 1px solid var(--border-dim);
  border-radius: 6px;
  background: var(--bg-app);
  padding: 8px 12px;
}
.item-row { display: flex; justify-content: space-between; align-items: center; }
.item-left { display: flex; align-items: center; gap: 8px; cursor: pointer; flex: 1; }
.item-right { display: flex; align-items: center; gap: 8px; }

.chevron { width: 16px; height: 16px; color: var(--txt-tertiary); transition: transform 0.2s; display: flex; }
.chevron.rot { transform: rotate(90deg); }
.chevron.tiny { width: 12px; height: 12px; }

.score-input {
  width: 40px; text-align: center;
  background: var(--bg-panel); border: 1px solid var(--border-dim);
  border-radius: 4px; font-family: "JetBrains Mono"; font-size: 12px;
  color: var(--brand); font-weight: 600;
}

.item-desc {
  margin-top: 8px; padding-left: 24px; padding-right: 40px;
  border-top: 1px dashed var(--border-dim);
  padding-top: 8px;
}

.add-sub-btn {
  width: 100%; margin-top: 12px;
  border: 1px dashed var(--border-dim);
  background: transparent; color: var(--txt-tertiary);
  padding: 6px; border-radius: 6px; font-size: 12px;
  cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 6px;
}
.add-sub-btn:hover { border-color: var(--brand); color: var(--brand); background: var(--brand-dim); }

/* Preview Pane */
.ide-preview {
  width: 320px;
  border-left: 1px solid var(--border-dim);
  background: var(--bg-panel);
  display: flex; flex-direction: column;
}
.preview-header {
  height: 40px; display: flex; align-items: center; justify-content: space-between;
  padding: 0 12px; border-bottom: 1px solid var(--border-dim);
  font-size: 12px; font-weight: 600; color: var(--txt-secondary);
}
.preview-content {
  flex: 1; overflow-y: auto; padding: 16px;
  display: flex; flex-direction: column; gap: 16px;
}

.preview-meta {
  display: grid; grid-template-columns: 1fr 1fr; gap: 12px;
  background: var(--bg-app); padding: 12px; border-radius: 8px; border: 1px solid var(--border-dim);
}
.meta-item { display: flex; flex-direction: column; gap: 4px; }
.meta-item label { font-size: 10px; color: var(--txt-tertiary); text-transform: uppercase; }
.meta-item .value { font-family: "JetBrains Mono"; font-size: 14px; font-weight: 600; color: var(--txt-primary); }

.code-block { display: flex; flex-direction: column; gap: 6px; }
.code-label { font-size: 11px; color: var(--txt-tertiary); }
.code-content {
  background: var(--bg-app); border: 1px solid var(--border-dim);
  border-radius: 6px; padding: 12px;
  font-family: "JetBrains Mono"; font-size: 11px; line-height: 1.5;
  color: var(--txt-secondary); white-space: pre-wrap; word-break: break-all;
  max-height: 300px; overflow-y: auto;
}

/* Utils */
.icon-btn {
  background: transparent; border: none; color: var(--txt-tertiary); cursor: pointer;
  padding: 6px; border-radius: 4px; display: flex; align-items: center; justify-content: center;
}
.icon-btn:hover { color: var(--txt-primary); background: var(--bg-hover); }
.icon-btn.danger:hover { color: var(--error); background: var(--error-bg); }
.icon-btn.tiny { width: 24px; height: 24px; padding: 0; }

.list-anim-enter-active, .list-anim-leave-active { transition: all 0.3s var(--ease-spring); }
.list-anim-enter-from, .list-anim-leave-to { opacity: 0; transform: translateY(-10px); }

@media (max-width: 900px) {
  .ide-body { flex-direction: column; }
  .ide-sidebar { width: 100%; height: auto; max-height: 150px; }
  .ide-preview { position: fixed; inset: 0; width: 100%; height: 100%; z-index: 100; }
}

</style>