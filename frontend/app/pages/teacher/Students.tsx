import { useEffect, useState } from "react";

import { TextUI } from "@/shared/components/UI/TextUI";
import { PageLayout } from "@/shared/components/Layouts/PageLayout";
import { fetchStudents, type StudentResponse } from "@/shared/api/students";

export default function Students() {
  const [students, setStudents] = useState<StudentResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    fetchStudents()
      .then((response) => setStudents(response.data))
      .catch(() => setHasError(true))
      .finally(() => setIsLoading(false));
  }, []);

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
            <div
              key={student.id}
              className="bg-white border border-gray-300 p-4"
            >
              <TextUI variant="normal" title={student.fullname}>
                <span className="line-clamp-1">{student.fullname}</span>
              </TextUI>
              <TextUI variant="desc" className="mt-1">
                ID: {student.id}
              </TextUI>
            </div>
          ))}
        </div>
      )}
    </PageLayout>
  );
}
