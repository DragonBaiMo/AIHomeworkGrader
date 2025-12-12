<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import type { PromptCategory, PromptConfig, PromptSection } from "@/api/types";

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

const editable = ref<PromptConfig | null>(null);
const currentKey = ref<string>("");
const collapsedModules = reactive(new Set<number>()); // 模块折叠状态
// 使用字符串 "moduleIdx-itemIdx" 来记录细则折叠状态
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
  if (Object.keys(editable.value.categories).length <= 1) return alert("至少保留一个分类");
  if (!confirm("确定删除此分类吗？")) return;
  delete editable.value.categories[key];
  if (currentKey.value === key) currentKey.value = Object.keys(editable.value.categories)[0];
}

function addSection() {
  currentCategory.value?.sections.push({ key: "维度名称", max_score: 10, items: [] });
}
function removeSection(idx: number) { currentCategory.value?.sections.splice(idx, 1); }

function addItem(section: PromptSection, mIdx: number) {
  section.items.push({ key: "评分点", max_score: 5, description: "" });
  // Auto expand new item
  expandedItems.add(`${mIdx}-${section.items.length - 1}`);
}
function removeItem(section: PromptSection, idx: number) { section.items.splice(idx, 1); }
function handleSave() { if (editable.value) emit("save", JSON.parse(JSON.stringify(editable.value))); }
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
                  <span class="tag mobile-hide">满分</span>
                  <input type="number" class="transparent-input num" v-model.number="section.max_score" />
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
