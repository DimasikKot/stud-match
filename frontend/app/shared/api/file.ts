import api, { errorValidate } from "@/shared/api/axios";

// ===== Типы =====
export interface FileResponse {
  id: number;
  name: string;
  object_key: string;
  path: string;
  size: number;
  created_at: string;
  updated_at: string;
}

export interface FileListResponse extends FileResponse {
  is_labeled?: boolean;
  total_rows?: number | null;
  prediction_model?: {
    id: number;
    name: string;
    parameters: Record<string, unknown>;
  } | null;
  origin_file?: {
    id: number;
    name: string;
  } | null;
}

export interface MessageResponse {
  success: boolean;
  detail: string;
}

const BACKEND_URL =
  import.meta.env.VITE_BACKEND_URL ?? "https://localhost/backend/api/v1";

export const fileDownloadUrl = (fileId: number) =>
  `${BACKEND_URL}/files/${fileId}/download`;

export const fileViewUrl = (fileId: number) =>
  `${BACKEND_URL}/files/${fileId}/view`;

export const uploadFiles = async (files: File[]): Promise<FileResponse[]> => {
  try {
    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));
    const { data } = await api.post<FileResponse[]>("/files/", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  } catch (error) {
    errorValidate(error);
    throw error;
  }
};

export const fetchFiles = async (
  projectId?: number | string,
): Promise<{ data: FileListResponse[] }> => {
  try {
    const { data } = await api.get<{ data: FileListResponse[] }>("/files/", {
      params: projectId !== undefined ? { project_id: projectId } : {},
    });
    return data;
  } catch (error) {
    errorValidate(error);
    throw error;
  }
};

export const deleteFile = async (fileId: number): Promise<MessageResponse> => {
  try {
    const { data } = await api.delete<MessageResponse>(`/files/${fileId}`);
    return data;
  } catch (error) {
    errorValidate(error);
    throw error;
  }
};
