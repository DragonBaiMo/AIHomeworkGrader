import { onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { fetchPromptConfig, gradeHomework, savePromptConfig } from "@/api/client";
import type { GradeConfigPayload, GradeResponse, PromptConfig, PromptSettings, TemplateOption } from "@/api/types";
import { useUI } from "@/shared/composables/useUI";

type TabKey = "workspace" | "rules" | "templates" | "settings";
type Theme = "dark" | "light";

const STORAGE_KEY = "ai-grader-pro-config";
const THEME_KEY = "ai-grader-theme";
const WORKSPACE_STATE_KEY = "ai-grader-workspace-state-v1";

type WorkspaceCachePayload = {
  version: 1;
  savedAt: number;
  inProgress: boolean;
  statusText: string;
  result: GradeResponse | null;
};

export function useAppController() {
  const { showToast, confirm } = useUI();
  const activeTab = ref<TabKey>("workspace");
  const theme = ref<Theme>("dark");
  const statusText = ref("就绪");
  const loading = ref(false);
  const gradeSessionId = ref(0);

  const config = reactive<GradeConfigPayload>({
    apiUrl: "",
    apiKey: "",
    modelName: "",
    multiEnabled: false,
    models: [],
    template: "auto",
    mock: false,
    skipFormatCheck: true,
    scoreTargetMax: 60,
  });

  const configPersistTimer = ref<number | null>(null);

  const result = ref<GradeResponse | null>(null);
  const promptConfig = ref<PromptConfig | null>(null);
  const promptLoading = ref(false);
  const promptSaving = ref(false);
  const promptError = ref("");

  const defaultTemplate: TemplateOption = {
    label: "自动识别",
    value: "auto",
  };
  const templateOptions = ref<TemplateOption[]>([defaultTemplate]);

  const PROMPT_SETTINGS_KEY = "ai-grader-prompt-settings";
  const promptSettings = reactive<PromptSettings>({
    autoSaveEnabled: true,
    autoSaveIntervalSeconds: 60,
  });

  function updateConfig(payload: Partial<GradeConfigPayload>) {
    Object.assign(config, payload);
  }

  function updatePromptSettings(payload: Partial<PromptSettings>) {
    if (typeof payload.autoSaveEnabled === "boolean") {
      promptSettings.autoSaveEnabled = payload.autoSaveEnabled;
    }
    if (typeof payload.autoSaveIntervalSeconds === "number" && payload.autoSaveIntervalSeconds > 0) {
      promptSettings.autoSaveIntervalSeconds = payload.autoSaveIntervalSeconds;
    }
  }

  function loadPromptSettings() {
    const cache = localStorage.getItem(PROMPT_SETTINGS_KEY);
    if (!cache) return;
    try {
      const parsed = JSON.parse(cache) as PromptSettings;
      promptSettings.autoSaveEnabled = parsed.autoSaveEnabled ?? promptSettings.autoSaveEnabled;
      if (parsed.autoSaveIntervalSeconds && parsed.autoSaveIntervalSeconds > 0) {
        promptSettings.autoSaveIntervalSeconds = parsed.autoSaveIntervalSeconds;
      }
    } catch {
      /* ignore */
    }
  }

  function sanitizeResultForCache(payload: GradeResponse): GradeResponse {
    return {
      ...payload,
      items: (payload.items || []).map((item) => ({
        ...item,
        raw_response: null,
      })),
    };
  }

  function persistWorkspaceState(inProgress: boolean) {
    const payload: WorkspaceCachePayload = {
      version: 1,
      savedAt: Date.now(),
      inProgress,
      statusText: statusText.value,
      result: result.value ? sanitizeResultForCache(result.value) : null,
    };
    try {
      localStorage.setItem(WORKSPACE_STATE_KEY, JSON.stringify(payload));
    } catch {
      showToast("批改结果过大，无法缓存到本地存储。", "warning");
    }
  }

  function clearWorkspaceState() {
    result.value = null;
    statusText.value = "就绪";
    localStorage.removeItem(WORKSPACE_STATE_KEY);
  }

  function loadWorkspaceState() {
    const cache = localStorage.getItem(WORKSPACE_STATE_KEY);
    if (!cache) return;
    try {
      const parsed = JSON.parse(cache) as WorkspaceCachePayload;
      if (parsed.version !== 1) return;
      if (parsed.result) result.value = parsed.result;
      if (typeof parsed.statusText === "string" && parsed.statusText.trim()) {
        statusText.value = parsed.statusText;
      }
      if (parsed.inProgress) {
        statusText.value = "上次批改在页面刷新时被中断，请重新点击开始批改。";
        showToast(statusText.value, "warning");
        persistWorkspaceState(false);
      }
    } catch {
      /* ignore */
    }
  }

  function toggleTheme() {
    theme.value = theme.value === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", theme.value);
    localStorage.setItem(THEME_KEY, theme.value);
  }

  function initTheme() {
    const saved = localStorage.getItem(THEME_KEY) as Theme | null;
    if (saved) {
      theme.value = saved;
    } else {
      const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      theme.value = prefersDark ? "dark" : "light";
    }
    document.documentElement.setAttribute("data-theme", theme.value);
  }

  function loadFromStorage() {
    const cache = localStorage.getItem(STORAGE_KEY);
    if (!cache) return;
    try {
      const saved = JSON.parse(cache) as Partial<GradeConfigPayload>;
      updateConfig({
        apiUrl: saved.apiUrl || "",
        apiKey: saved.apiKey || "",
        modelName: saved.modelName || "",
        multiEnabled: Boolean(saved.multiEnabled),
        models: Array.isArray(saved.models) && saved.models.length
          ? saved.models.map((m: any) => ({
              api_url: String(m?.api_url || ""),
              api_key: String(m?.api_key || ""),
              model_name: String(m?.model_name || ""),
            }))
          : [],
        template: saved.template || defaultTemplate.value,
        mock: Boolean(saved.mock),
        skipFormatCheck: saved.skipFormatCheck !== false,
        scoreTargetMax: typeof saved.scoreTargetMax === "number" ? saved.scoreTargetMax : 60,
      });
    } catch {
      /* ignore */
    }
  }

  watch(
    () => ({ ...config }),
    (val) => {
      if (configPersistTimer.value !== null) {
        window.clearTimeout(configPersistTimer.value);
      }
      configPersistTimer.value = window.setTimeout(() => {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(val));
        configPersistTimer.value = null;
      }, 200);
    },
    { deep: true },
  );

  watch(
    () => ({ ...promptSettings }),
    (val) => {
      localStorage.setItem(PROMPT_SETTINGS_KEY, JSON.stringify(val));
    },
    { deep: true },
  );

  onBeforeUnmount(() => {
    if (configPersistTimer.value !== null) {
      window.clearTimeout(configPersistTimer.value);
      configPersistTimer.value = null;
    }
  });

  async function loadPromptConfig() {
    promptLoading.value = true;
    try {
      const cfg = await fetchPromptConfig();
      if (!cfg) {
        promptConfig.value = {
          system_prompt: "",
          categories: {
            default: {
              display_name: "默认分类",
              sections: [],
              docx_validation: {
                enabled: false,
                allowed_font_keywords: [],
                allowed_font_size_pts: [],
                font_size_tolerance: 0.5,
                target_line_spacing: null,
                line_spacing_tolerance: null,
              },
            },
          },
        };
        promptError.value = "提示词配置为空，已加载默认配置";
        rebuildTemplateOptions(promptConfig.value);
        showToast(promptError.value, "warning");
        return;
      }
      promptConfig.value = cfg;
      rebuildTemplateOptions(cfg);
    } catch (err) {
      promptError.value = (err as Error).message;
      rebuildTemplateOptions(null);
    } finally {
      promptLoading.value = false;
    }
  }

  function rebuildTemplateOptions(cfg: PromptConfig | null) {
    if (!cfg) {
      templateOptions.value = [defaultTemplate];
      if (!config.template) config.template = defaultTemplate.value;
      return;
    }
    const list = Object.entries(cfg.categories).map(([key, cat]) => ({
      label: cat.display_name || key,
      value: key,
    }));
    templateOptions.value = [defaultTemplate, ...(list.length ? list : [])];

    if (!templateOptions.value.some((t) => t.value === config.template)) {
      config.template = templateOptions.value[0].value;
    }
  }

  async function handleGrade(files: File[]) {
    if (loading.value) return;
    const currentSession = bumpGradeSession();
    loading.value = true;
    statusText.value = "处理中";
    persistWorkspaceState(true);
    try {
      const resp = await gradeHomework(files, config);
      if (currentSession !== gradeSessionId.value) return;
      result.value = resp;
      statusText.value = "已完成";
      persistWorkspaceState(false);
      showToast(`批改完成！成功处理 ${resp.success_count} 个文件`, "success");
    } catch (err) {
      if (currentSession !== gradeSessionId.value) return;
      statusText.value = "异常";
      persistWorkspaceState(false);
      showToast((err as Error).message, "error");
    } finally {
      if (currentSession !== gradeSessionId.value) return;
      loading.value = false;
    }
  }

  async function handleSavePrompt(payload: PromptConfig) {
    promptSaving.value = true;
    try {
      await savePromptConfig(payload);
      promptConfig.value = payload;
      rebuildTemplateOptions(payload);
      showToast("配置已保存", "success");
    } catch (err) {
      showToast((err as Error).message, "error");
    } finally {
      promptSaving.value = false;
    }
  }

  function bumpGradeSession(): number {
    gradeSessionId.value += 1;
    return gradeSessionId.value;
  }

  function resetConfigToDefaults() {
    updateConfig({
      apiUrl: "",
      apiKey: "",
      modelName: "",
      multiEnabled: false,
      models: [],
      template: defaultTemplate.value,
      mock: false,
      skipFormatCheck: true,
      scoreTargetMax: 60,
    });
  }

  function resetPromptSettingsToDefaults() {
    promptSettings.autoSaveEnabled = true;
    promptSettings.autoSaveIntervalSeconds = 60;
  }

  function clearAllLocalCache() {
    confirm({
      title: "清除本地缓存",
      content: "确定要清除批改缓存吗？这将清空当前批改结果与工作台状态（不影响系统设置与规则编辑器设置），且无法恢复。",
      confirmText: "立即清除",
      type: "danger",
      onConfirm: () => {
        executeClearCache();
      },
    });
  }

  function executeClearCache() {
    bumpGradeSession();
    loading.value = false;
    statusText.value = "就绪";
    result.value = null;

    try {
      localStorage.removeItem(WORKSPACE_STATE_KEY);
    } catch {
      /* ignore */
    }
    showToast("批改缓存已清除", "success");
  }

  onMounted(() => {
    initTheme();
    loadFromStorage();
    loadPromptSettings();
    loadWorkspaceState();
    loadPromptConfig();
  });

  return {
    activeTab,
    theme,
    statusText,
    loading,
    result,
    promptConfig,
    promptLoading,
    promptSaving,
    promptError,
    templateOptions,
    promptSettings,
    toggleTheme,
    updateConfig,
    updatePromptSettings,
    handleGrade,
    clearWorkspaceState,
    clearAllLocalCache,
    loadPromptConfig,
    handleSavePrompt,
    resetConfigToDefaults,
    resetPromptSettingsToDefaults,
    executeClearCache,
    config,
  };
}
