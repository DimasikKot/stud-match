import api, { errorValidate } from "@/shared/api/axios";
import type { ZipResponse } from "@/shared/api/zips";

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
  status: (typeof FileStatus)[keyof typeof FileStatus];
  skills_vector: Record<string, unknown>;
  zip_id: number;
  student_fullname: string | null;
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

const UPLOAD_BATCH_LIMIT = 20 * 1024 * 1024;

export const uploadFiles = async (
  files: File[],
  onProgress?: (fileIndex: number, progress: number) => void,
): Promise<ZipResponse[]> => {
  const items = files.map((file, index) => ({ file, index }));
  items.sort((a, b) => a.file.size - b.file.size);

  const batches: (typeof items)[] = [];
  let current: (typeof items)[] = [];
  let currentSize = 0;
  for (const item of items) {
    if (item.file.size > UPLOAD_BATCH_LIMIT) {
      if (current.length > 0) {
        batches.push(current);
        current = [];
        currentSize = 0;
      }
      batches.push([item]);
      continue;
    }
    if (
      currentSize + item.file.size > UPLOAD_BATCH_LIMIT &&
      current.length > 0
    ) {
      batches.push(current);
      current = [];
      currentSize = 0;
    }
    current.push(item);
    currentSize += item.file.size;
  }
  if (current.length > 0) {
    batches.push(current);
  }

  const results: ZipResponse[] = [];
  try {
    for (const batch of batches) {
      const formData = new FormData();
      batch.forEach(({ file }) => formData.append("files", file));
      const { data } = await api.post<ZipResponse[]>("/zips/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (event) => {
          if (event.total) {
            const progress = Math.round((event.loaded / event.total) * 100);
            batch.forEach(({ index }) => onProgress?.(index, progress));
          }
        },
      });
      results.push(...data);
      batch.forEach(({ index }) => onProgress?.(index, 100));
    }
    return results;
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
