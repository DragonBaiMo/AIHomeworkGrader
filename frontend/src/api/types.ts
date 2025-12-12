export interface GradeConfigPayload {
  apiUrl: string;
  apiKey: string;
  modelName: string;
  template: string;
  mock: boolean;
  skipFormatCheck: boolean;
}

export interface GradeItem {
  file_name: string;
  student_id: string | null;
  student_name: string | null;
  score: number | null;
  dimension_structure: number | null;
  dimension_content: number | null;
  dimension_expression: number | null;
  comment: string | null;
  status: string;
  error_message: string | null;
  raw_text_length: number;
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
}

export interface PromptSection {
  key: string;
  max_score: number;
  items: PromptItem[];
}

export interface PromptCategory {
  display_name: string;
  sections: PromptSection[];
}

export interface PromptConfig {
  system_prompt: string;
  categories: Record<string, PromptCategory>;
}

export interface TemplateOption {
  label: string;
  value: string;
}
