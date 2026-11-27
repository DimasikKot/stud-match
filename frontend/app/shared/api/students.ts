import api, { errorValidate } from "@/shared/api/axios";

export interface StudentResponse {
  id: number;
  fullname: string;
}

export interface StudentListResponse {
  data: StudentResponse[];
}

export interface StudentFileResponse {
  id: number;
  name: string;
  size: number;
  status: string;
  zip_id: number;
}

export interface StudentDetailResponse {
  id: number;
  fullname: string;
  skills_set: Record<string, unknown>;
  model_version: string;
  files: StudentFileResponse[];
}

export const fetchStudents = async (): Promise<StudentListResponse> => {
  try {
    const { data } = await api.get<StudentListResponse>("/students/");
    return data;
  } catch (error) {
    errorValidate(error);
    throw error;
  }
};

export const fetchStudent = async (
  studentId: number,
): Promise<StudentDetailResponse> => {
  try {
    const { data } = await api.get<StudentDetailResponse>(
      `/students/${studentId}`,
    );
    return data;
  } catch (error) {
    errorValidate(error);
    throw error;
  }
};
