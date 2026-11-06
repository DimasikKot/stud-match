import toast from "react-hot-toast";

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

const BACKEND_URL =
  import.meta.env.VITE_BACKEND_URL ?? "https://localhost/backend/api/v1";

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

// axios в браузере не умеет читать ответ по частям, поэтому стрим через fetch
export const streamLLMTask = async (
  taskId: string,
  onChunk: (chunk: string) => void,
  signal?: AbortSignal,
): Promise<void> => {
  const response = await fetch(`${BACKEND_URL}/llms/tasks/${taskId}/stream`, {
    credentials: "include",
    signal,
  });

  if (!response.ok || !response.body) {
    const errorText = `Ошибка стрима ${response.status}`;
    toast.error(errorText);
    throw new Error(errorText);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    onChunk(decoder.decode(value, { stream: true }));
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
