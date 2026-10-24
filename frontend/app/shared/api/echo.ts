import api, { errorValidate } from "@/shared/api/axios";

export interface GetEchoResponse {
  detail: string;
  success: boolean;
}

export const fetchBackendEcho = async (): Promise<
  GetEchoResponse | undefined
> => {
  try {
    const response = await api.get<GetEchoResponse>("/echos/health");
    return response.data;
  } catch (error: unknown) {
    errorValidate(error);
  }
};
