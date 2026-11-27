import api, { errorValidate } from "@/shared/api/axios";

export interface ProjectResponse {
  id: number;
  name: string;
  description: string;
  updated_at: string;
}

export interface ProjectDetailResponse extends ProjectResponse {
  constraints_set: Record<string, unknown>;
  skills_set: Record<string, unknown>;
  model_version: string;
}

export interface ProjectListResponse {
  data: ProjectResponse[];
}

export interface ProjectRequest {
  name: string;
  description: string;
  constraints_set?: Record<string, unknown>;
  skills_set?: Record<string, unknown>;
}

export const fetchProjects = async (params?: {
  sort?: string;
  search?: string;
}): Promise<ProjectListResponse> => {
  try {
    const { data } = await api.get<ProjectListResponse>("/projects/", {
      params,
    });
    return data;
  } catch (error) {
    errorValidate(error);
    throw error;
  }
};

export const fetchProject = async (
  projectId: number,
): Promise<ProjectDetailResponse> => {
  try {
    const { data } = await api.get<ProjectDetailResponse>(
      `/projects/${projectId}`,
    );
    return data;
  } catch (error) {
    errorValidate(error);
    throw error;
  }
};

export const createProject = async (
  payload: ProjectRequest,
): Promise<ProjectDetailResponse> => {
  try {
    const { data } = await api.post<ProjectDetailResponse>(
      "/projects/",
      payload,
    );
    return data;
  } catch (error) {
    errorValidate(error);
    throw error;
  }
};

export const updateProject = async (
  projectId: number,
  payload: ProjectRequest,
): Promise<ProjectDetailResponse> => {
  try {
    const { data } = await api.patch<ProjectDetailResponse>(
      `/projects/${projectId}`,
      payload,
    );
    return data;
  } catch (error) {
    errorValidate(error);
    throw error;
  }
};

export const deleteProject = async (projectId: number): Promise<void> => {
  try {
    await api.delete(`/projects/${projectId}`);
  } catch (error) {
    errorValidate(error);
    throw error;
  }
};
