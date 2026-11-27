import api, { errorValidate } from "@/shared/api/axios";

export interface SkillResponse {
  id: number;
  name: string;
}

export interface SkillListResponse {
  data: SkillResponse[];
}

export const fetchSkills = async (): Promise<SkillListResponse> => {
  try {
    const { data } = await api.get<SkillListResponse>("/skills/");
    return data;
  } catch (error) {
    errorValidate(error);
    throw error;
  }
};

export const createSkill = async (name: string): Promise<SkillResponse> => {
  try {
    const { data } = await api.post<SkillResponse>("/skills/", { name });
    return data;
  } catch (error) {
    errorValidate(error);
    throw error;
  }
};

export const deleteSkill = async (skillId: number): Promise<void> => {
  try {
    await api.delete(`/skills/${skillId}`);
  } catch (error) {
    errorValidate(error);
    throw error;
  }
};
