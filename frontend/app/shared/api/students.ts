import api, { errorValidate } from "@/shared/api/axios";

export interface StudentResponse {
  id: number;
  fullname: string;
}

export interface StudentListResponse {
  data: StudentResponse[];
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
