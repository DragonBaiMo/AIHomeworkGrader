import { ref } from "vue";
import type { GradeConfigPayload, PromptSettings } from "@/api/types";
import { Icons } from "../ui/icons";

export function useSettingsPanel(
  props: {
    config: GradeConfigPayload;
    promptSettings: PromptSettings;
  },
  emit: {
    (e: "update:config", payload: Partial<GradeConfigPayload>): void;
    (e: "update:promptSettings", payload: Partial<PromptSettings>): void;
    (e: "submit"): void;
  },
) {
  const localConfig = ref({ ...props.config });

  function handleChange<T extends keyof GradeConfigPayload>(key: T, value: GradeConfigPayload[T]) {
    localConfig.value[key] = value;
    emit("update:config", { [key]: value });
  }

  function handleToggleMulti(enabled: boolean) {
    handleChange("multiEnabled", enabled as any);
    if (enabled) {
      const models = Array.isArray(localConfig.value.models) ? [...localConfig.value.models] : [];
      if (models.length === 0) {
        models.push({ api_url: "", api_key: "", model_name: "" });
        localConfig.value.models = models;
        emit("update:config", { models });
      }
    }
  }

  function handleModelChange(index: number, key: "api_url" | "api_key" | "model_name", value: string) {
    const models = Array.isArray(localConfig.value.models) ? [...localConfig.value.models] : [];
    while (models.length <= index) {
      models.push({ api_url: "", api_key: "", model_name: "" });
    }
    const current = { ...(models[index] as any) };
    current[key] = value;
    models[index] = current;
    localConfig.value.models = models;
    emit("update:config", { models });
  }

  function addModelRow() {
    const models = Array.isArray(localConfig.value.models) ? [...localConfig.value.models] : [];
    if (models.length >= 2) return;
    models.push({ api_url: "", api_key: "", model_name: "" });
    localConfig.value.models = models;
    emit("update:config", { models });
  }

  function removeModelRow(index: number) {
    const models = Array.isArray(localConfig.value.models) ? [...localConfig.value.models] : [];
    if (models.length <= 1) return;
    models.splice(index, 1);
    localConfig.value.models = models;
    emit("update:config", { models });
  }

  function handlePromptSetting<T extends keyof PromptSettings>(key: T, value: PromptSettings[T]) {
    emit("update:promptSettings", { [key]: value });
  }

  return {
    Icons,
    localConfig,
    handleChange,
    handleToggleMulti,
    handleModelChange,
    addModelRow,
    removeModelRow,
    handlePromptSetting,
  };
}
