import type { GradeConfigPayload, GradeResponse, PromptConfig } from "./types";

const API_PREFIX = "/api";

async function parseJsonSafe(resp: Response): Promise<any> {
  try {
    return await resp.json();
  } catch {
    return null;
  }
}

export async function gradeHomework(files: File[], config: GradeConfigPayload): Promise<GradeResponse> {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  formData.append("api_url", config.apiUrl);
  formData.append("api_key", config.apiKey);
  formData.append("model_name", config.modelName);
  if (config.multiEnabled) {
    const models = (config.models || []).slice(0, 2).map((m) => ({
      api_url: m.api_url || "",
      api_key: m.api_key || "",
      model_name: m.model_name || "",
    }));
    if (models.length > 0) {
      formData.append("models", JSON.stringify(models));
    }
  }
  formData.append("template", config.template);
  formData.append("mock", String(config.mock));
  formData.append("skip_format_check", String(config.skipFormatCheck));
  formData.append("score_target_max", String(config.scoreTargetMax));

  const resp = await fetch(`${API_PREFIX}/grade`, {
    method: "POST",
    body: formData,
  });

  if (!resp.ok) {
    const payload = await parseJsonSafe(resp);
    const message = payload?.detail || "批改请求失败，请稍后重试。";
    throw new Error(message);
  }

  return resp.json();
}

export async function fetchPromptConfig(): Promise<PromptConfig | null> {
  const resp = await fetch(`${API_PREFIX}/prompt-config`);
  if (!resp.ok) {
    throw new Error("获取提示词配置失败");
  }
  const data = await resp.json();
  return data?.config ?? null;
}

export async function savePromptConfig(payload: PromptConfig): Promise<void> {
  const resp = await fetch(`${API_PREFIX}/prompt-config`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!resp.ok) {
    const data = await parseJsonSafe(resp);
    const message = data?.detail || "保存提示词配置失败";
    throw new Error(message);
  }
}

export async function fetchPromptPreview(promptConfig: PromptConfig, categoryKey: string, scoreTargetMax: number): Promise<{ system_prompt: string; user_prompt: string; score_rubric_max: number; score_target_max: number; }> {
  const resp = await fetch(`${API_PREFIX}/prompt-preview`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      prompt_config: promptConfig,
      category_key: categoryKey,
      score_target_max: scoreTargetMax,
    }),
  });

  if (!resp.ok) {
    if (resp.status === 404) {
      throw new Error("提示词预览接口不存在，请重启后端服务。");
    }
    const data = await parseJsonSafe(resp);
    const message = data?.detail || "获取提示词预览失败";
    throw new Error(message);
  }
  return resp.json();
}

export async function fetchPromptTemplates(): Promise<Record<string, string>> {
  const resp = await fetch(`${API_PREFIX}/prompt-templates`);
  if (!resp.ok) {
    throw new Error("获取提示词模板失败");
  }
  const data = await resp.json();
  return data?.sections ?? {};
}

export async function savePromptTemplates(sections: Record<string, string>): Promise<void> {
  const resp = await fetch(`${API_PREFIX}/prompt-templates`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ sections }),
  });

  if (!resp.ok) {
    const data = await parseJsonSafe(resp);
    const message = data?.detail || "保存提示词模板失败";
    throw new Error(message);
  }
}
