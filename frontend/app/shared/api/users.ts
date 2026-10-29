import api, { errorValidate } from "@/shared/api/axios";

// ===== Типы =====
export interface UserRequest {
  email: string;
  password: string;
}

export interface UserResponse {
  id: number;
  email: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface MessageResponse {
  message: string;
}

export const registerUser = async (
  payload: UserRequest,
): Promise<UserResponse> => {
  try {
    const { data } = await api.post<UserResponse>("/users/register", payload);
    return data;
  } catch (error) {
    errorValidate(error);
    throw error;
  }
};

export const loginUser = async (
  payload: UserRequest,
): Promise<TokenResponse> => {
  try {
    const { data } = await api.post<TokenResponse>("/users/login", payload);
    return data; // access_token в теле можно игнорировать — он уже в httpOnly-куке
  } catch (error) {
    errorValidate(error);
    throw error;
  }
};

export const refreshTokens = async (): Promise<TokenResponse> => {
  const { data } = await api.post<TokenResponse>("/users/refresh");
  return data;
};

export const logoutUser = async (): Promise<MessageResponse> => {
  try {
    const { data } = await api.post<MessageResponse>("/users/logout");
    return data;
  } catch (error) {
    errorValidate(error);
    throw error;
  }
};

export const getCurrentUser = async (): Promise<UserResponse> => {
  try {
    const { data } = await api.get<UserResponse>("/users/me");
    return data;
  } catch (error) {
    errorValidate(error);
    throw error;
  }
};
