import api, { errorValidate } from "@/shared/api/axios";

export const FileStatus = {
  NotExtracted: "not_extracted",
  Queued: "queued",
  Extracting: "extracting",
  Extracted: "extracted",
  Applied: "applied",
} as const;

export interface FileResponse {
  id: number;
  name: string;
  size: number;
  rustfs_object_key: string;
  rustfs_bucket: string;
  status: (typeof FileStatus)[keyof typeof FileStatus];
  skills_vector: Record<string, unknown>;
  work_date: string;
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

export const fetchFiles = async (): Promise<{ data: FileResponse[] }> => {
  try {
    const { data } = await api.get<{ data: FileResponse[] }>("/files/");
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
