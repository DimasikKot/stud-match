import api, { errorValidate } from "@/shared/api/axios";

export interface GetHealthResponse {
  detail: string;
  success: boolean;
}

export const fetchBackendHealth = async (): Promise<
  GetHealthResponse | undefined
> => {
  try {
    const response = await api.get<GetHealthResponse>("/healths/health");
    return response.data;
  } catch (error: unknown) {
    errorValidate(error);
  }
};
