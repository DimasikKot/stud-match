import api, { errorValidate } from "@/shared/api/axios";

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  fullname: string;
  email: string;
  password: string;
}

export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
}

export interface UserResponse {
  id: number;
  fullname: string;
  email: string;
  role: string;
  skills_vector: Record<string, unknown>;
}

export interface UserListResponse {
  data: UserResponse[];
}

export interface MessageResponse {
  message: string;
}

export const registerUser = async (
  payload: RegisterRequest,
): Promise<UserResponse> => {
  try {
    const { data } = await api.post<UserResponse>("/users/register", payload);
    return data;
  } catch (error) {
    errorValidate(error);
    throw error;
  }
};

export const fetchUsers = async (): Promise<UserListResponse> => {
  try {
    const { data } = await api.get<UserListResponse>("/users/");
    return data;
  } catch (error) {
    errorValidate(error);
    throw error;
  }
};

export const loginUser = async (
  payload: LoginRequest,
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
    sessionStorage.setItem("fullname", data.fullname);
    sessionStorage.setItem("email", data.email);
    sessionStorage.setItem("role", data.role);
    return data;
  } catch (error) {
    errorValidate(error);
    throw error;
  }
};

export const changePassword = async (
  payload: ChangePasswordRequest,
): Promise<MessageResponse> => {
  try {
    const { data } = await api.patch<MessageResponse>(
      "/users/me/password",
      payload,
    );
    return data;
  } catch (error) {
    errorValidate(error);
    throw error;
  }
};
