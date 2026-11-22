import api, { errorValidate } from "@/shared/api/axios";

export interface UserRequest {
  email: string;
  password: string;
}

export interface UserResponse {
  id: number;
  email: string;
  role: string;
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
): Promise<UserResponse> => {
  try {
    const { data } = await api.post<UserResponse>("/users/login", payload);
    return data;
  } catch (error) {
    errorValidate(error);
    throw error;
  }
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
    sessionStorage.setItem("username", data.email);
    sessionStorage.setItem("email", data.email);
    sessionStorage.setItem("role", data.role);
    return data;
  } catch (error) {
    errorValidate(error);
    throw error;
  }
};
