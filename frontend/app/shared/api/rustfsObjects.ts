import api, { errorValidate } from "@/shared/api/axios";
import type { MessageResponse } from "@/shared/api/file";

export const RustfsObjectStatus = {
  NotExtracted: "not_extracted",
  Queued: "queued",
  Extracting: "extracting",
  Failed: "failed",
  Extracted: "extracted",
} as const;

export type RustfsObjectStatusValue =
  (typeof RustfsObjectStatus)[keyof typeof RustfsObjectStatus];

export interface RustfsObjectResponse {
  id: number;
  object_key: string;
  status: RustfsObjectStatusValue;
  feature_set: Record<string, unknown>;
  model_version: string;
}

export interface RustfsObjectsResponse {
  count: number;
  data: RustfsObjectResponse[];
}

export const fetchRustfsObjects = async (
  status: RustfsObjectStatusValue,
): Promise<RustfsObjectsResponse | undefined> => {
  try {
    const { data } = await api.get<RustfsObjectsResponse>(
      `/rustfs-objects/?status=${status}`,
    );
    return data;
  } catch (error) {
    errorValidate(error);
  }
};

export const extractFeatures = async (
  status: RustfsObjectStatusValue = RustfsObjectStatus.NotExtracted,
): Promise<MessageResponse | undefined> => {
  try {
    const { data } = await api.post<MessageResponse>(
      `/rustfs-objects/extract-features?status=${status}`,
    );
    return data;
  } catch (error) {
    errorValidate(error);
  }
};
