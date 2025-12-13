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
const headerRefreshing = ref(false); // Local state for header refresh spin
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
  currentCategory.value?.sections.unshift({ key: "新维度", max_score: 10, items: [] });
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

function handleHeaderRefresh() {
  headerRefreshing.value = true;
  emit('refresh');
  setTimeout(() => { headerRefreshing.value = false; }, 600);
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
        <!-- Added spin class logic -->
        <button 
          class="action-btn glass-icon-btn" 
          @click="handleHeaderRefresh" 
          title="重置"
        >
          <span :class="{ 'spin-icon': headerRefreshing }" v-html="Icons.Refresh"></span>
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
          <span v-if="saving" class="loader-spinner-sm"></span>
          <span v-else v-html="Icons.Save"></span>
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
        
        <div class="editor-stage">
          <!-- Top Row: Split Config -->
          <div class="stage-row">
            <!-- Left: Identity -->
            <section class="glass-card identity-card">
              <div class="card-header">
                <span class="card-label">基础设定</span>
                <button class="icon-action danger tiny" @click="removeCategory(currentKey)" title="删除分类">
                   <span v-html="Icons.Trash"></span>
                </button>
              </div>
              
              <div class="field-stack">
                 <div class="field-group">
                   <label>分类名称</label>
                   <input type="text" v-model="currentCategory.display_name" class="clean-input-lg" placeholder="e.g. 职业规划书" />
                 </div>
                 <div class="field-group">
                   <label>AI 角色 (System Prompt)</label>
                   <textarea
                     v-model="editable.system_prompt"
                     rows="3"
                     class="clean-textarea"
                     placeholder="定义 AI 在评估时的角色与视角..."
                   ></textarea>
                 </div>
              </div>
            </section>

            <!-- Right: Constraints (Docx) -->
            <section class="glass-card constraint-card" :class="{ 'is-active': docxValidationEnabled }">
              <div class="card-header">
                 <div class="header-main">
                   <span class="card-label">格式约束</span>
                   <span class="status-dot" :class="{ active: docxValidationEnabled }"></span>
                 </div>
                 <label class="ios-switch">
                    <input type="checkbox" v-model="docxValidationEnabled" />
                    <div class="switch-body"><div class="switch-knob"></div></div>
                 </label>
              </div>
              
              <div class="constraint-body">
                 <p class="hint-text" v-if="!docxValidationEnabled">
                   启用后，将强制校验文档的字体与字号，不符合规范的作业将被标记异常。
                 </p>
                 <div v-else class="params-grid animate-in">
                    <div class="param-item">
                      <label>允许字体</label>
                      <input type="text" v-model="docxAllowedFontsText" class="param-input" placeholder="宋体, 黑体" />
                    </div>
                    <div class="param-item">
                      <label>允许字号 (pt)</label>
                      <input type="text" v-model="docxAllowedSizesText" class="param-input" placeholder="12, 14" />
                    </div>
                    <div class="param-item">
                      <label>容差 (±)</label>
                      <input type="number" v-model.number="docxFontSizeTolerance" class="param-input" step="0.1" />
                    </div>
                 </div>
              </div>
            </section>
          </div>

          <!-- Bottom Row: Rubric Canvas -->
          <div class="rubric-canvas-container">
             <div class="canvas-header">
                <div class="header-left">
                  <h3 class="canvas-title">评分细则</h3>
                  <span class="canvas-subtitle">Rubric & Criteria</span>
                </div>
                <!-- Enhanced Button -->
                <button class="bento-btn primary sm" @click.stop="addSection">
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
                           <div class="item-header" @click="toggleItem(sIdx, iIdx)">
                              <div class="item-title-row">
                                 <span class="item-chevron" :class="{ open: isItemExpanded(sIdx, iIdx) }" v-html="Icons.ChevronRight"></span>
                                 <div class="input-wrapper" @click.stop>
                                   <input type="text" v-model="item.key" class="invisible-input item-input" placeholder="评分点" />
                                 </div>
                              </div>
                              <div class="item-meta" @click.stop>
                                 <input type="number" v-model.number="item.max_score" class="score-input-mini" />
                                 <button class="mini-btn" @click="removeItem(section, iIdx)"><span v-html="Icons.Trash"></span></button>
                              </div>
                           </div>
                           
                           <div class="item-body" v-show="isItemExpanded(sIdx, iIdx)">
                             <textarea 
                               v-model="item.description" 
                               class="desc-textarea" 
                               placeholder="详细的评分标准描述..."
                               @click.stop
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
        </div>
      </main>

      <!-- Preview Rail -->
      <aside v-if="previewOpen" class="preview-rail">
        <div class="rail-header">
          <span class="rail-label">实时预览</span>
          <button class="icon-btn-refresh" @click="refreshPreview">
             <span :class="{ 'spin-icon': previewLoading }" v-html="Icons.Refresh"></span>
          </button>
        </div>
        
        <div class="preview-body custom-scrollbar">
          <div v-if="previewLoading && !previewSystemPrompt" class="skeleton-loader">
             <div class="sk-line w-50"></div>
             <div class="sk-box"></div>
             <div class="sk-box"></div>
          </div>

          <div v-else-if="previewError" class="error-banner">
             {{ previewError }}
          </div>

          <div v-else>
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
                <pre class="code-view">{{ previewSystemPrompt || '(空)' }}</pre>
              </div>
               <div class="code-card">
                <div class="code-header">User Prompt</div>
                <pre class="code-view">{{ previewUserPrompt || '(空)' }}</pre>
              </div>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped src="./prompt-editor.css"></style>
