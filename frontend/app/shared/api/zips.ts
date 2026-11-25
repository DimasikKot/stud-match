import api, { errorValidate } from "@/shared/api/axios";
import type { MessageResponse } from "@/shared/api/file";

export const ZipStatus = {
  Pending: "pending",
  Processing: "processing",
  Completed: "completed",
  Failed: "failed",
} as const;

export interface ZipResponse {
  id: number;
  name: string;
  status: (typeof ZipStatus)[keyof typeof ZipStatus];
  date: string;
  files_count: number;
}

export interface ZipFileResponse {
  id: number;
  name: string;
  size: number;
  status: string;
  student_fullname: string | null;
}

export interface ZipDetailResponse extends ZipResponse {
  files: ZipFileResponse[];
}

export const fetchZips = async (): Promise<{ data: ZipResponse[] }> => {
  try {
    const { data } = await api.get<{ data: ZipResponse[] }>("/zips/");
    return data;
  } catch (error) {
    errorValidate(error);
    throw error;
  }
};

export const fetchZip = async (zipId: number): Promise<ZipDetailResponse> => {
  try {
    const { data } = await api.get<ZipDetailResponse>(`/zips/${zipId}`);
    return data;
  } catch (error) {
    errorValidate(error);
    throw error;
  }
};

export const deleteZip = async (zipId: number): Promise<MessageResponse> => {
  try {
    const { data } = await api.delete<MessageResponse>(`/zips/${zipId}`);
    return data;
  } catch (error) {
    errorValidate(error);
    throw error;
  }
};
