import api, { errorValidate } from "@/shared/api/axios";

export interface ProjectResponse {
  id: number;
  name: string;
  description: string;
  updated_at: string;
}

export interface ProjectListResponse {
  data: ProjectResponse[];
}

export const fetchProjects = async (): Promise<ProjectListResponse> => {
  try {
    const { data } = await api.get<ProjectListResponse>("/projects/");
    return data;
  } catch (error) {
    errorValidate(error);
    throw error;
  }
};
