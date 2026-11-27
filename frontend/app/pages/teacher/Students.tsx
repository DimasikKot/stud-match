import { useEffect, useState } from "react";

import { TextUI } from "@/shared/components/UI/TextUI";
import { PageLayout } from "@/shared/components/Layouts/PageLayout";
import { StudentCard } from "@/shared/components/StudentCard";
import { StudentDetailsModal } from "@/shared/components/StudentDetailsModal";
import {
  fetchStudent,
  fetchStudents,
  type StudentDetailResponse,
  type StudentResponse,
} from "@/shared/api/students";

export default function Students() {
  const [students, setStudents] = useState<StudentResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  const [selectedStudentId, setSelectedStudentId] = useState<number | null>(
    null,
  );
  const [studentDetails, setStudentDetails] =
    useState<StudentDetailResponse | null>(null);
  const [isDetailsLoading, setIsDetailsLoading] = useState(false);
  const [hasDetailsError, setHasDetailsError] = useState(false);

  useEffect(() => {
    fetchStudents()
      .then((response) => setStudents(response.data))
      .catch(() => setHasError(true))
      .finally(() => setIsLoading(false));
  }, []);

  const loadStudentDetails = (studentId: number) => {
    setStudentDetails(null);
    setHasDetailsError(false);
    setIsDetailsLoading(true);
    fetchStudent(studentId)
      .then(setStudentDetails)
      .catch(() => setHasDetailsError(true))
      .finally(() => setIsDetailsLoading(false));
  };

  const openStudent = (studentId: number) => {
    setSelectedStudentId(studentId);
    loadStudentDetails(studentId);
  };

  return (
    <PageLayout title="Студенты">
      <TextUI variant="header" className="mb-4">
        Студенты ({students.length})
      </TextUI>

      {isLoading ? (
        <div className="bg-white border border-gray-300 text-center">
          <TextUI variant="desc">Загрузка...</TextUI>
        </div>
      ) : hasError ? (
        <div className="bg-white border border-gray-300 text-center">
          <TextUI variant="desc">Не удалось загрузить список студентов</TextUI>
        </div>
      ) : students.length === 0 ? (
        <div className="bg-white border border-gray-300 text-center">
          <TextUI variant="desc">Студентов пока нет</TextUI>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {students.map((student) => (
            <StudentCard
              key={student.id}
              student={student}
              onClick={() => openStudent(student.id)}
            />
          ))}
        </div>
      )}

      {selectedStudentId !== null && (
        <StudentDetailsModal
          student={studentDetails}
          isLoading={isDetailsLoading}
          hasError={hasDetailsError}
          onClose={() => setSelectedStudentId(null)}
          onChanged={() => {
            if (selectedStudentId !== null) {
              loadStudentDetails(selectedStudentId);
            }
          }}
        />
      )}
    </PageLayout>
  );
}
