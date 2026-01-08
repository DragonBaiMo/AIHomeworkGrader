export interface GradeConfigPayload {
  apiUrl: string;
  apiKey: string;
  modelName: string;
  multiEnabled: boolean;
  models: ModelEndpointPayload[];
  template: string;
  mock: boolean;
  skipFormatCheck: boolean;
  scoreTargetMax: number;
}

export interface ModelEndpointPayload {
  api_url: string;
  api_key?: string;
  model_name: string;
}

export interface GradeItem {
  file_name: string;
  student_id: string | null;
  student_name: string | null;
  score: number | null;
  score_rubric_max: number | null;
  score_rubric: number | null;
  detail_json: string | null;
  comment: string | null;
  status: string;
  error_message: string | null;
  raw_text_length: number;
  raw_response: string | null;
  aggregate_strategy?: string | null;
  grader_results?: any[] | null;
}

export interface GradeResponse {
  batch_id: string;
  total_files: number;
  success_count: number;
  error_count: number;
  average_score: number | null;
  download_result_url: string;
  download_error_url: string;
  items: GradeItem[];
}

export interface PromptItem {
  key: string;
  max_score: number;
  description: string;
  is_deduction?: boolean;
}

export interface PromptSection {
  key: string;
  max_score: number;
  items: PromptItem[];
}

export interface DocxValidationConfig {
  enabled: boolean;
  allowed_font_keywords: string[];
  allowed_font_size_pts: number[];
  font_size_tolerance?: number;
  target_line_spacing?: number | null;
  line_spacing_tolerance?: number | null;
}

export interface PromptCategory {
  display_name: string;
  docx_validation?: DocxValidationConfig;
  sections: PromptSection[];
  score_target_max?: number;
}

export interface PromptConfig {
  system_prompt: string;
  categories: Record<string, PromptCategory>;
}

export interface TemplateOption {
  label: string;
  value: string;
}

export interface PromptSettings {
  autoSaveEnabled: boolean;
  autoSaveIntervalSeconds: number;
}

export interface RubricGenerateRequest {
  description: string;
  api_url: string;
  api_key?: string;
  model_name: string;
  total_score?: number;
}

export interface RubricGenerateResponse {
  rubric: PromptCategory & { category_key: string };
  total_score: number;
  message: string;
}

// SSE 流式批改事件类型
export interface SSEInitEvent {
  batch_id: string;
  total_files: number;
}

export interface SSEProgressEvent {
  current: number;
  total: number;
  percent: number;
}

export interface SSEItemEvent {
  item: GradeItem;
  index: number;
}

export interface SSECompleteEvent {
  batch_id: string;
  total_files: number;
  success_count: number;
  error_count: number;
  average_score: number | null;
  download_result_url: string;
  download_error_url: string;
}

export interface SSEErrorEvent {
  message: string;
  recoverable: boolean;
}

export interface GradeStreamCallbacks {
  onInit: (data: SSEInitEvent) => void;
  onProgress: (data: SSEProgressEvent) => void;
  onItem: (data: SSEItemEvent) => void;
  onComplete: (data: SSECompleteEvent) => void;
  onError: (data: SSEErrorEvent) => void;
}
