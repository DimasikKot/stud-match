import api, { errorValidate } from "@/shared/api/axios";

// ===== Типы =====
export type LLMTaskStatus = "queued" | "running" | "done" | "error";

export interface LLMTaskCreate {
  prompt: string;
  file_ids: number[];
  enable_thinking?: boolean;
  max_new_tokens?: number;
}

export interface LLMTaskResponse {
  task_id: string;
  status: LLMTaskStatus;
  result: string;
  error: string;
}

export const createLLMTask = async (
  body: LLMTaskCreate,
): Promise<LLMTaskResponse> => {
  try {
    const { data } = await api.post<LLMTaskResponse>("/llms/tasks", body);
    return data;
  } catch (error) {
    errorValidate(error);
    throw error;
  }
};

export const fetchLLMTask = async (
  taskId: string,
): Promise<LLMTaskResponse> => {
  try {
    const { data } = await api.get<LLMTaskResponse>(`/llms/tasks/${taskId}`);
    return data;
  } catch (error) {
    errorValidate(error);
    throw error;
  }
};

// Делит ответ Qwen на рассуждения (<think>...</think>) и сам ответ
export const splitThinking = (
  text: string,
): { thinking: string; answer: string } => {
  const start = text.indexOf("<think>");
  if (start === -1) return { thinking: "", answer: text };
  const end = text.indexOf("</think>", start);
  if (end === -1)
    return { thinking: text.slice(start + "<think>".length), answer: "" };
  return {
    thinking: text.slice(start + "<think>".length, end).trim(),
    answer: text.slice(end + "</think>".length).trim(),
  };
};
