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
  formData.append("template", config.template);
  formData.append("mock", String(config.mock));
  formData.append("skip_format_check", String(config.skipFormatCheck));

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
