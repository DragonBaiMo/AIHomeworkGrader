<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import type { DocxValidationConfig, PromptCategory, PromptConfig, PromptSection } from "@/api/types";
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

function ensureDocxValidation(category: PromptCategory): DocxValidationConfig {
  if (!category.docx_validation) {
    category.docx_validation = {
      enabled: false,
      allowed_font_keywords: [],
      allowed_font_size_pts: [],
      font_size_tolerance: 0.5,
      target_line_spacing: null,
      line_spacing_tolerance: null,
    };
  }
  if (typeof category.docx_validation.font_size_tolerance !== "number") {
    category.docx_validation.font_size_tolerance = 0.5;
  }
  return category.docx_validation;
}

const docxValidationEnabled = computed<boolean>({
  get() {
    if (!currentCategory.value) return false;
    return Boolean(ensureDocxValidation(currentCategory.value).enabled);
  },
  set(val) {
    if (!currentCategory.value) return;
    ensureDocxValidation(currentCategory.value).enabled = Boolean(val);
  },
});

const docxAllowedFontsText = computed<string>({
  get() {
    if (!currentCategory.value) return "";
    const cfg = ensureDocxValidation(currentCategory.value);
    return (cfg.allowed_font_keywords || []).join(",");
  },
  set(val) {
    if (!currentCategory.value) return;
    const cfg = ensureDocxValidation(currentCategory.value);
    cfg.allowed_font_keywords = String(val || "")
      .split(/[,，]/g)
      .map((x) => x.trim())
      .filter((x) => x.length > 0);
  },
});

const docxAllowedSizesText = computed<string>({
  get() {
    if (!currentCategory.value) return "";
    const cfg = ensureDocxValidation(currentCategory.value);
    return (cfg.allowed_font_size_pts || []).join(",");
  },
  set(val) {
    if (!currentCategory.value) return;
    const cfg = ensureDocxValidation(currentCategory.value);
    const sizes = String(val || "")
      .split(/[,，]/g)
      .map((x) => x.trim())
      .filter((x) => x.length > 0)
      .map((x) => Number(x))
      .filter((x) => Number.isFinite(x) && x > 0);
    cfg.allowed_font_size_pts = Array.from(new Set(sizes));
  },
});

const docxFontSizeTolerance = computed<number>({
  get() {
    if (!currentCategory.value) return 0.5;
    const cfg = ensureDocxValidation(currentCategory.value);
    return Number.isFinite(cfg.font_size_tolerance as number) ? Number(cfg.font_size_tolerance) : 0.5;
  },
  set(val) {
    if (!currentCategory.value) return;
    const cfg = ensureDocxValidation(currentCategory.value);
    const num = Number(val);
    cfg.font_size_tolerance = Number.isFinite(num) && num >= 0 ? num : 0.5;
  },
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
  editable.value.categories[key] = {
    display_name: "新分类",
    sections: [],
    docx_validation: {
      enabled: false,
      allowed_font_keywords: [],
      allowed_font_size_pts: [],
      font_size_tolerance: 0.5,
      target_line_spacing: null,
      line_spacing_tolerance: null,
    },
  };
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
  for (const cat of Object.values(editable.value.categories)) {
    const docxCfg = ensureDocxValidation(cat);
    if (docxCfg.enabled) {
      if (!docxCfg.allowed_font_keywords?.length) {
        showToast("已启用 docx 格式校验，但未配置允许字体", "error");
        return;
      }
      if (!docxCfg.allowed_font_size_pts?.length) {
        showToast("已启用 docx 格式校验，但未配置允许字号（pt）", "error");
        return;
      }
    }
    cat.sections.forEach((sec) => (sec.max_score = getSectionTotal(sec)));
  }
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
  <div class="studio-layout animate-in">
    <!-- Studio Header -->
    <header class="studio-header">
      <div class="header-left">
        <div class="icon-badge">
          <span v-html="Icons.FileCode"></span>
        </div>
        <span class="studio-title">规则编辑器</span>
      </div>
      <div class="header-actions">
        <button class="action-btn ghost" @click="emit('refresh')" title="重置">
          <span v-html="Icons.Refresh"></span>
        </button>
        <button 
          class="action-btn toggle" 
          :class="{ active: previewOpen }" 
          @click="previewOpen = !previewOpen; if(previewOpen) refreshPreview();"
        >
          <span v-html="Icons.Eye"></span>
          <span>预览</span>
        </button>
        <button class="action-btn primary" :disabled="saving || !editable" @click="handleSave">
          <span v-html="Icons.Save"></span>
          <span>{{ saving ? "保存中..." : "保存" }}</span>
        </button>
      </div>
    </header>

    <div class="studio-body" v-if="editable">
      <!-- Navigation Rail -->
      <aside class="nav-rail glass-morphism">
        <div class="rail-header">
          <span class="rail-label">分类列表</span>
          <button class="icon-btn-add" @click="addCategory"><span v-html="Icons.Plus"></span></button>
        </div>
        <div class="rail-list custom-scrollbar">
          <button
            v-for="(cat, key) in editable.categories"
            :key="key"
            class="nav-item"
            :class="{ active: currentKey === key }"
            @click="currentKey = String(key)"
          >
            <span class="nav-icon" v-html="Icons.Folder"></span>
            <span class="nav-text">{{ cat.display_name || key }}</span>
          </button>
        </div>
      </aside>

      <!-- Main Canvas -->
      <main class="canvas-area custom-scrollbar" v-if="currentCategory">
        
        <!-- Meta Configuration Card -->
        <section class="config-card">
          <div class="card-row header-row">
            <div class="field-group grow">
              <label class="field-label">分类名称</label>
              <input type="text" v-model="currentCategory.display_name" class="modern-input bold" />
            </div>
            <button class="icon-action danger" @click="removeCategory(currentKey)">
              <span v-html="Icons.Trash"></span>
            </button>
          </div>
          
          <div class="card-row">
            <div class="field-group block">
              <label class="field-label">AI 角色设定 (System Prompt)</label>
              <textarea
                v-model="editable.system_prompt"
                rows="2"
                class="modern-textarea"
                placeholder="定义 AI 在评估时的角色与视角..."
              ></textarea>
            </div>
          </div>
        </section>

        <!-- Docx Validation Module (The requested focus) -->
        <section class="feature-module" :class="{ 'is-active': docxValidationEnabled }">
          <div class="module-header">
            <div class="module-title-group">
               <div class="status-indicator"></div>
               <span class="module-title">文档格式校验</span>
               <span class="module-subtitle">Docx Formatting Strict Mode</span>
            </div>
            
            <label class="ios-switch">
              <input type="checkbox" v-model="docxValidationEnabled" />
              <div class="switch-body">
                <div class="switch-knob"></div>
              </div>
            </label>
          </div>

          <div class="module-content" v-if="docxValidationEnabled">
            <div class="grid-params">
              <div class="param-cell">
                <label>允许字体 <span class="sub">(Keywords)</span></label>
                <input type="text" v-model="docxAllowedFontsText" class="param-input" placeholder="e.g. 宋体, SimSun" />
              </div>
              <div class="param-cell">
                <label>允许字号 <span class="sub">(Points)</span></label>
                <input type="text" v-model="docxAllowedSizesText" class="param-input" placeholder="e.g. 12, 14" />
              </div>
              <div class="param-cell small">
                <label>字号容差 <span class="sub">(±pt)</span></label>
                <input type="number" v-model.number="docxFontSizeTolerance" class="param-input mono" min="0" step="0.1" />
              </div>
            </div>
            <div class="module-hint">
              <span class="info-icon">i</span>
              启用后，所有提交的 .docx 文件必须符合上述格式要求，否则将被标记为异常。
            </div>
          </div>
        </section>

        <!-- Rules Canvas -->
        <div class="rubric-canvas">
          <div class="canvas-actions">
            <span class="section-heading">评分维度 & 细则</span>
            <button class="btn-create" @click="addSection">
              <span v-html="Icons.Plus"></span> 新增维度
            </button>
          </div>

          <div class="rubric-stack">
             <TransitionGroup name="stack-anim">
              <div 
                v-for="(section, sIdx) in currentCategory.sections" 
                :key="sIdx"
                class="rubric-block"
                :class="{ collapsed: collapsedModules.has(sIdx) }"
              >
                <!-- Block Header -->
                <div class="block-bar" @click="toggleModule(sIdx)">
                   <div class="bar-left">
                     <span class="collapse-icon" :class="{ open: !collapsedModules.has(sIdx) }" v-html="Icons.ChevronRight"></span>
                     <input type="text" v-model="section.key" class="invisible-input title-input" placeholder="维度名称" @click.stop />
                   </div>
                   <div class="bar-right">
                     <span class="score-tag">{{ getSectionTotal(section) }} PTS</span>
                     <button class="mini-btn danger" @click.stop="removeSection(sIdx)"><span v-html="Icons.Trash"></span></button>
                   </div>
                </div>

                <!-- Block Body -->
                <div class="block-content" v-show="!collapsedModules.has(sIdx)">
                  <div class="items-list">
                    <div v-for="(item, iIdx) in section.items" :key="iIdx" class="item-card">
                       <div class="item-header">
                          <div class="item-title-row" @click="toggleItem(sIdx, iIdx)">
                             <span class="item-chevron" :class="{ open: isItemExpanded(sIdx, iIdx) }" v-html="Icons.ChevronRight"></span>
                             <input type="text" v-model="item.key" class="invisible-input item-input" placeholder="评分点" @click.stop />
                          </div>
                          <div class="item-meta">
                             <input type="number" v-model.number="item.max_score" class="score-input-mini" />
                             <button class="mini-btn" @click="removeItem(section, iIdx)"><span v-html="Icons.Trash"></span></button>
                          </div>
                       </div>
                       
                       <div class="item-body" v-show="isItemExpanded(sIdx, iIdx)">
                         <textarea 
                           v-model="item.description" 
                           class="desc-textarea" 
                           placeholder="详细的评分标准描述..."
                         ></textarea>
                       </div>
                    </div>
                  </div>
                  
                  <button class="btn-add-item" @click="addItem(section, sIdx)">
                    <span class="plus-sign">+</span> 添加评分细则
                  </button>
                </div>
              </div>
             </TransitionGroup>
          </div>
        </div>
      </main>

      <!-- Preview Rail -->
      <aside v-if="previewOpen" class="preview-rail">
        <div class="rail-header">
          <span class="rail-label">实时预览</span>
          <button class="icon-btn-refresh" @click="refreshPreview"><span v-html="Icons.Refresh"></span></button>
        </div>
        
        <div class="preview-body custom-scrollbar">
          <div class="meta-grid">
             <div class="meta-field">
               <label>目标满分</label>
               <input type="number" v-model.number="previewScoreTargetMax" class="meta-input" @change="refreshPreview" />
             </div>
             <div class="meta-field read-only">
               <label>规则总分</label>
               <span class="meta-value">{{ previewRubricMax ?? "-" }}</span>
             </div>
          </div>
          
          <div class="code-card">
            <div class="code-header">System Prompt</div>
            <pre class="code-view">{{ previewSystemPrompt }}</pre>
          </div>
           <div class="code-card">
            <div class="code-header">User Prompt</div>
            <pre class="code-view">{{ previewUserPrompt }}</pre>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
/* --- Global Studio Theme --- */
.studio-layout {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-app);
  color: var(--txt-primary);
  border-radius: var(--radius-l);
  overflow: hidden;
  /* 隐形纹理 */
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.02'/%3E%3C/svg%3E");
}

/* --- Header --- */
.studio-header {
  height: 64px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-dim);
  background: var(--bg-panel);
}
.header-left { display: flex; align-items: center; gap: 12px; }
.icon-badge {
  width: 32px; height: 32px;
  background: var(--brand-dim);
  color: var(--brand);
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
}
.studio-title {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.header-actions { display: flex; gap: 12px; }
.action-btn {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px; font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s;
}
.action-btn.ghost { background: transparent; color: var(--txt-tertiary); padding: 8px; }
.action-btn.ghost:hover { background: var(--bg-hover); color: var(--txt-primary); }
.action-btn.toggle { background: var(--bg-active); color: var(--txt-secondary); border-color: var(--border-dim); }
.action-btn.toggle.active { background: var(--brand-dim); color: var(--brand); border-color: var(--brand); }
.action-btn.primary { background: var(--brand); color: #fff; box-shadow: 0 4px 12px rgba(var(--brand-rgb), 0.2); }
.action-btn.primary:hover { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(var(--brand-rgb), 0.3); }

/* --- Body Layout --- */
.studio-body { display: flex; flex: 1; overflow: hidden; }

/* --- Nav Rail --- */
.nav-rail {
  width: 260px;
  background: var(--bg-panel);
  border-right: 1px solid var(--border-dim);
  display: flex; flex-direction: column;
}
.rail-header {
  padding: 16px 20px;
  display: flex; justify-content: space-between; align-items: center;
  border-bottom: 1px solid var(--border-dim);
}
.rail-label { font-size: 11px; font-weight: 700; color: var(--txt-tertiary); text-transform: uppercase; letter-spacing: 0.05em; }
.icon-btn-add {
  width: 24px; height: 24px;
  border-radius: 6px;
  border: 1px solid var(--border-dim);
  background: var(--bg-app);
  color: var(--txt-secondary);
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
}
.icon-btn-add:hover { border-color: var(--brand); color: var(--brand); }

.rail-list { padding: 12px; display: flex; flex-direction: column; gap: 4px; overflow-y: auto; }
.nav-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  border: none; background: transparent;
  color: var(--txt-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
  text-align: left;
}
.nav-item:hover { background: var(--bg-hover); color: var(--txt-primary); }
.nav-item.active { background: var(--bg-active); color: var(--brand); font-weight: 600; }
.nav-icon { opacity: 0.7; }
.nav-item.active .nav-icon { opacity: 1; }

/* --- Canvas Area --- */
.canvas-area {
  flex: 1;
  padding: 32px 40px;
  overflow-y: auto;
  display: flex; flex-direction: column; gap: 32px;
  background: linear-gradient(180deg, var(--bg-app) 0%, var(--bg-panel) 100%);
}

/* Config Card */
.config-card {
  background: var(--bg-panel);
  border: 1px solid var(--border-dim);
  border-radius: 16px;
  padding: 24px;
  display: flex; flex-direction: column; gap: 20px;
  box-shadow: 0 4px 6px -2px rgba(0,0,0,0.02);
}
.card-row { display: flex; gap: 16px; align-items: flex-end; }
.header-row { border-bottom: 1px dashed var(--border-dim); padding-bottom: 20px; }
.field-group { display: flex; flex-direction: column; gap: 8px; }
.field-group.grow { flex: 1; }
.field-group.block { width: 100%; }

.field-label { font-size: 11px; font-weight: 600; color: var(--txt-tertiary); text-transform: uppercase; }
.modern-input {
  background: var(--bg-app);
  border: 1px solid var(--border-dim);
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 14px;
  color: var(--txt-primary);
  transition: all 0.2s;
  font-family: 'JetBrains Mono', monospace;
}
.modern-input.bold { font-weight: 600; font-size: 15px; }
.modern-input:focus, .modern-textarea:focus { border-color: var(--brand); box-shadow: 0 0 0 3px var(--brand-dim); outline: none; }

.modern-textarea {
  background: var(--bg-app);
  border: 1px solid var(--border-dim);
  border-radius: 8px;
  padding: 12px;
  font-size: 13px;
  line-height: 1.6;
  color: var(--txt-secondary);
  resize: vertical;
  font-family: inherit;
}

.icon-action {
  width: 36px; height: 36px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 8px;
  border: 1px solid var(--border-dim);
  background: var(--bg-app);
  cursor: pointer;
  color: var(--txt-tertiary);
  transition: all 0.2s;
}
.icon-action:hover { border-color: var(--error); color: var(--error); background: var(--error-bg); }

/* --- Feature Module (Docx) --- */
.feature-module {
  border: 1px solid var(--border-dim);
  border-radius: 16px;
  background: var(--bg-panel);
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.feature-module.is-active {
  border-color: var(--brand);
  background: linear-gradient(to bottom, var(--bg-panel), var(--bg-active));
  box-shadow: 0 10px 30px -10px rgba(var(--brand-rgb), 0.15);
}

.module-header {
  padding: 20px 24px;
  display: flex; justify-content: space-between; align-items: center;
  border-bottom: 1px solid transparent;
}
.feature-module.is-active .module-header { border-bottom-color: var(--border-dim); }

.module-title-group { display: flex; align-items: center; gap: 12px; }
.status-indicator {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--txt-tertiary);
  transition: all 0.3s;
}
.feature-module.is-active .status-indicator {
  background: var(--brand);
  box-shadow: 0 0 8px var(--brand);
}
.module-title { font-size: 15px; font-weight: 600; color: var(--txt-primary); }
.module-subtitle { font-size: 12px; color: var(--txt-tertiary); font-family: 'JetBrains Mono'; }

/* iOS Switch */
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

.module-content {
  padding: 24px;
  animation: slideDown 0.3s ease-out;
}
.grid-params {
  display: grid;
  grid-template-columns: 1fr 1fr 0.8fr;
  gap: 20px;
  margin-bottom: 16px;
}
.param-cell { display: flex; flex-direction: column; gap: 8px; }
.param-cell label { font-size: 12px; font-weight: 500; color: var(--txt-secondary); }
.param-cell .sub { color: var(--txt-tertiary); font-size: 10px; }

.param-input {
  background: var(--bg-app);
  border: 1px solid var(--border-dim);
  border-radius: 8px;
  padding: 8px 12px;
  font-family: 'JetBrains Mono';
  font-size: 13px;
  color: var(--txt-primary);
  transition: all 0.2s;
}
.param-input:focus { border-color: var(--brand); box-shadow: 0 0 0 2px var(--brand-dim); outline: none; }

.module-hint {
  display: flex; align-items: center; gap: 10px;
  font-size: 12px; color: var(--txt-tertiary);
  background: var(--bg-app);
  padding: 10px 14px;
  border-radius: 8px;
}
.info-icon {
  width: 16px; height: 16px; background: var(--txt-tertiary); color: var(--bg-app);
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-weight: bold; font-size: 10px;
}

/* --- Rubric Canvas --- */
.rubric-canvas { margin-top: 16px; display: flex; flex-direction: column; gap: 20px; }
.canvas-actions { display: flex; justify-content: space-between; align-items: center; }
.section-heading { font-size: 14px; font-weight: 700; color: var(--txt-secondary); text-transform: uppercase; letter-spacing: 0.05em; }
.btn-create {
  background: var(--bg-active); border: 1px solid var(--border-dim);
  color: var(--txt-primary); font-size: 12px; font-weight: 600;
  padding: 6px 16px; border-radius: 8px; cursor: pointer;
  display: flex; align-items: center; gap: 6px;
  transition: all 0.2s;
}
.btn-create:hover { border-color: var(--brand); color: var(--brand); }

.rubric-stack { display: flex; flex-direction: column; gap: 16px; }

.rubric-block {
  background: var(--bg-panel);
  border-radius: 12px;
  border: 1px solid var(--border-dim);
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
  transition: all 0.3s;
}
.rubric-block:hover { box-shadow: 0 8px 24px -6px rgba(0,0,0,0.06); transform: translateY(-2px); }
.rubric-block.collapsed { background: var(--bg-app); transform: none; box-shadow: none; border-style: dashed; }

.block-bar {
  padding: 12px 20px;
  background: var(--bg-active);
  border-bottom: 1px solid var(--border-dim);
  display: flex; justify-content: space-between; align-items: center;
  cursor: pointer;
}
.rubric-block.collapsed .block-bar { border-bottom: none; background: transparent; }

.bar-left, .bar-right { display: flex; align-items: center; gap: 12px; }

.collapse-icon {
  width: 20px; height: 20px; color: var(--txt-tertiary);
  transition: transform 0.2s; display: flex; align-items: center; justify-content: center;
}
.collapse-icon.open { transform: rotate(90deg); }

.invisible-input {
  background: transparent; border: 1px solid transparent;
  color: var(--txt-primary); font-family: inherit;
  padding: 4px 8px; border-radius: 6px;
  transition: all 0.2s;
}
.invisible-input:hover { background: var(--bg-hover); }
.invisible-input:focus { background: var(--bg-app); border-color: var(--brand); outline: none; }
.invisible-input.title-input { font-weight: 700; font-size: 14px; width: 240px; }

.score-tag {
  font-family: 'JetBrains Mono'; font-size: 12px; font-weight: 600;
  background: var(--bg-app); padding: 4px 10px; border-radius: 6px;
  color: var(--txt-secondary); border: 1px solid var(--border-dim);
}

.mini-btn {
  width: 24px; height: 24px; border: none; background: transparent;
  color: var(--txt-tertiary); cursor: pointer; border-radius: 4px;
  display: flex; align-items: center; justify-content: center;
}
.mini-btn:hover { background: var(--bg-hover); color: var(--txt-primary); }
.mini-btn.danger:hover { background: var(--error-bg); color: var(--error); }

.block-content { padding: 20px; background: var(--bg-panel); }
.items-list { display: flex; flex-direction: column; gap: 12px; }

.item-card {
  background: var(--bg-app);
  border: 1px solid var(--border-dim);
  border-radius: 8px;
  overflow: hidden;
}
.item-header {
  padding: 8px 12px;
  display: flex; justify-content: space-between; align-items: center;
}
.item-title-row { display: flex; align-items: center; gap: 8px; flex: 1; cursor: pointer; }
.item-chevron { width: 14px; color: var(--txt-tertiary); transition: transform 0.2s; }
.item-chevron.open { transform: rotate(90deg); }
.item-input { font-size: 13px; width: 100%; }

.item-meta { display: flex; align-items: center; gap: 8px; }
.score-input-mini {
  width: 48px; text-align: center;
  background: var(--bg-panel); border: 1px solid var(--border-dim);
  border-radius: 4px; font-family: 'JetBrains Mono'; font-size: 12px;
  font-weight: 600; color: var(--brand);
}
.item-body {
  padding: 12px; border-top: 1px dashed var(--border-dim);
  background: var(--bg-app);
}
.desc-textarea {
  width: 100%; background: transparent; border: none;
  font-size: 13px; color: var(--txt-secondary);
  line-height: 1.5; resize: vertical; min-height: 40px;
}
.desc-textarea:focus { outline: none; }

.btn-add-item {
  margin-top: 16px; width: 100%;
  padding: 10px; border: 1px dashed var(--border-dim);
  background: transparent; color: var(--txt-tertiary);
  border-radius: 8px; cursor: pointer; font-size: 12px;
  transition: all 0.2s;
  display: flex; align-items: center; justify-content: center; gap: 8px;
}
.btn-add-item:hover { border-color: var(--brand); color: var(--brand); background: var(--brand-dim); }

/* --- Preview Rail --- */
.preview-rail {
  width: 320px;
  background: var(--bg-panel);
  border-left: 1px solid var(--border-dim);
  display: flex; flex-direction: column;
}
.icon-btn-refresh {
  width: 28px; height: 28px; border-radius: 6px;
  background: var(--bg-active); border: none; color: var(--txt-secondary);
  cursor: pointer; display: flex; align-items: center; justify-content: center;
}
.icon-btn-refresh:hover { color: var(--brand); }

.preview-body { padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 24px; }

.meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.meta-field { display: flex; flex-direction: column; gap: 6px; }
.meta-field label { font-size: 10px; color: var(--txt-tertiary); text-transform: uppercase; }
.meta-input {
  background: var(--bg-app); border: 1px solid var(--border-dim);
  padding: 6px; border-radius: 6px; font-family: 'JetBrains Mono';
  font-size: 13px; color: var(--txt-primary); width: 100%;
}
.meta-value {
  font-family: 'JetBrains Mono'; font-size: 16px; font-weight: 700;
  color: var(--txt-primary); display: block; padding-top: 4px;
}

.code-card { display: flex; flex-direction: column; gap: 8px; }
.code-header { font-size: 11px; font-weight: 600; color: var(--txt-tertiary); }
.code-view {
  background: var(--bg-app); border: 1px solid var(--border-dim);
  border-radius: 8px; padding: 12px;
  font-family: 'JetBrains Mono'; font-size: 11px; line-height: 1.5;
  color: var(--txt-secondary); white-space: pre-wrap; word-break: break-all;
}

@media (max-width: 1000px) {
  .studio-body { flex-direction: column; }
  .nav-rail { width: 100%; height: auto; max-height: 160px; border-right: none; border-bottom: 1px solid var(--border-dim); }
  .preview-rail { position: fixed; inset: 0; width: 100%; z-index: 200; }
  .grid-params { grid-template-columns: 1fr; }
}

/* Scrollbar */
.custom-scrollbar::-webkit-scrollbar { width: 6px; height: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: var(--border-dim); border-radius: 3px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: var(--txt-tertiary); }
</style>
