import api, { errorValidate } from "@/shared/api/axios";

export interface GetHealthResponse {
  success: boolean;
  detail: string;
  metrics: Record<string, unknown>;
}

export const fetchBackendHealth = async (): Promise<
  GetHealthResponse | undefined
> => {
  try {
    const response = await api.get<GetHealthResponse>("/healths/backend");
    return response.data;
  } catch (error: unknown) {
    errorValidate(error);
  }
};

export const fetchPostgresHealth = async (): Promise<
  GetHealthResponse | undefined
> => {
  try {
    const response = await api.get<GetHealthResponse>("/healths/postgres");
    return response.data;
  } catch (error: unknown) {
    errorValidate(error);
  }
};

export const fetchRedisHealth = async (): Promise<
  GetHealthResponse | undefined
> => {
  try {
    const response = await api.get<GetHealthResponse>("/healths/redis");
    return response.data;
  } catch (error: unknown) {
    errorValidate(error);
  }
};
