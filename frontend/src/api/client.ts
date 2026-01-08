import type {
  GradeConfigPayload,
  GradeResponse,
  GradeStreamCallbacks,
  PromptConfig,
  RubricGenerateRequest,
  RubricGenerateResponse,
  SSECompleteEvent,
  SSEErrorEvent,
  SSEInitEvent,
  SSEItemEvent,
  SSEProgressEvent,
} from "./types";

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

export async function generateRubric(request: RubricGenerateRequest): Promise<RubricGenerateResponse> {
  const resp = await fetch(`${API_PREFIX}/generate-rubric`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!resp.ok) {
    const data = await parseJsonSafe(resp);
    const message = data?.detail || "生成评分标准失败";
    throw new Error(message);
  }
  return resp.json();
}

/**
 * 构建批改请求的 FormData
 */
function buildGradeFormData(files: File[], config: GradeConfigPayload): FormData {
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
  return formData;
}

/**
 * 流式批改接口，通过 SSE 逐个返回批改结果
 * @returns AbortController 用于取消请求
 */
export function gradeHomeworkStream(
  files: File[],
  config: GradeConfigPayload,
  callbacks: GradeStreamCallbacks
): AbortController {
  const controller = new AbortController();
  const formData = buildGradeFormData(files, config);

  // 使用 fetch 发送 POST 请求并处理 SSE 流
  fetch(`${API_PREFIX}/grade-stream`, {
    method: "POST",
    body: formData,
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const data = await parseJsonSafe(response);
        const message = data?.detail || "流式批改请求失败";
        callbacks.onError({ message, recoverable: false });
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        callbacks.onError({ message: "无法获取响应流", recoverable: false });
        return;
      }

      const decoder = new TextDecoder();
      let buffer = "";
      let currentEvent = "";
      let currentData = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // 处理可能的 \r\n 换行符
        buffer = buffer.replace(/\r\n/g, "\n");

        // 按行分割，保留最后一行（可能不完整）放回 buffer
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmedLine = line.trim();

          if (trimmedLine.startsWith("event:")) {
            currentEvent = trimmedLine.slice(6).trim();
          } else if (trimmedLine.startsWith("data:")) {
            // 支持多行 data（追加）
            const dataContent = trimmedLine.slice(5).trim();
            if (currentData) {
              currentData += "\n" + dataContent;
            } else {
              currentData = dataContent;
            }
          } else if (trimmedLine === "" && currentData) {
            // 空行表示事件结束，触发分发
            try {
              const data = JSON.parse(currentData);
              switch (currentEvent) {
                case "init":
                  callbacks.onInit(data as SSEInitEvent);
                  break;
                case "progress":
                  callbacks.onProgress(data as SSEProgressEvent);
                  break;
                case "item":
                  callbacks.onItem(data as SSEItemEvent);
                  break;
                case "complete":
                  callbacks.onComplete(data as SSECompleteEvent);
                  break;
                case "error":
                  callbacks.onError(data as SSEErrorEvent);
                  break;
                default:
                  // 未知事件类型，尝试通用处理
                  console.warn("[SSE] Unknown event type:", currentEvent, data);
              }
            } catch (e) {
              console.error("[SSE] JSON parse error:", e, "data:", currentData);
            }
            currentEvent = "";
            currentData = "";
          }
        }
      }
      // 流结束后，如果还有未处理的数据，尝试处理
      if (currentData) {
        try {
          const data = JSON.parse(currentData);
          switch (currentEvent) {
            case "complete":
              callbacks.onComplete(data as SSECompleteEvent);
              break;
            case "error":
              callbacks.onError(data as SSEErrorEvent);
              break;
          }
        } catch {
          // 忽略
        }
      }
    })
    .catch((err) => {
      if (err.name === "AbortError") {
        // 用户主动取消
        return;
      }
      callbacks.onError({ message: err.message || "网络请求失败", recoverable: false });
    });

  return controller;
}
