import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";

import type { StudentDetailResponse } from "@/shared/api/students";
import { deleteFile, fileDownloadUrl, fileViewUrl } from "@/shared/api/file";
import { FileCard } from "@/shared/components/FileCard";
import { TextUI } from "@/shared/components/UI/TextUI";
import { ButtonUI } from "./UI/ButtonUI";
import { IconUI } from "./UI/IconUI";

export const StudentDetailsModal = ({
  student,
  isLoading,
  hasError,
  onClose,
  onChanged,
}: {
  student: StudentDetailResponse | null;
  isLoading: boolean;
  hasError: boolean;
  onClose: () => void;
  onChanged?: () => void;
}) => {
  const navigate = useNavigate();

  const handleDeleteFile = async (fileId: number) => {
    try {
      await deleteFile(fileId);
      toast.success("Файл удалён");
      onChanged?.();
    } catch {
      toast.error("Не удалось удалить файл");
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white border border-gray-300 w-full max-w-6xl max-h-[85vh]
          flex flex-col overflow-hidden"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-center justify-between gap-4 px-6 py-4 border-b border-gray-300">
          <div className="min-w-0">
            <TextUI variant="title" className="line-clamp-1">
              {student ? student.fullname : "Студент"}
            </TextUI>
            {student && (
              <TextUI variant="desc" className="mt-1">
                ID: {student.id} · Версия модели: {student.model_version}
              </TextUI>
            )}
          </div>

          <ButtonUI variant="icon" onClick={onClose} title="Закрыть">
            <IconUI size="24px" name="close" />
          </ButtonUI>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4 flex flex-col gap-6">
          {isLoading ? (
            <TextUI variant="desc">Загрузка...</TextUI>
          ) : hasError ? (
            <TextUI variant="error">
              Не удалось загрузить данные студента
            </TextUI>
          ) : student ? (
            <>
              <div>
                <TextUI variant="header" className="mb-2">
                  Словарь навыков
                </TextUI>
                {student.skills_set &&
                Object.keys(student.skills_set).length > 0 ? (
                  <pre
                    className="bg-gray-50 border border-gray-200 p-4 text-sm
                    font-mono whitespace-pre-wrap wrap-break-word max-h-64 overflow-y-auto"
                  >
                    {JSON.stringify(student.skills_set, null, 2)}
                  </pre>
                ) : (
                  <TextUI variant="desc">Словарь навыков пуст</TextUI>
                )}
              </div>

              <div>
                <TextUI variant="header" className="mb-2">
                  Привязанные файлы ({student.files.length})
                </TextUI>

                {student.files.length === 0 ? (
                  <TextUI variant="desc">Файлы не привязаны</TextUI>
                ) : (
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                    {student.files.map((file) => (
                      <FileCard
                        key={file.id}
                        file={{
                          id: file.id,
                          name: file.name,
                          status: file.status,
                          student_fullname: student.fullname,
                          feature_set: file.feature_set,
                        }}
                        onClick={() =>
                          window.open(fileViewUrl(file.id), "_blank")
                        }
                        onDownloadClick={() =>
                          window.open(fileDownloadUrl(file.id), "_blank")
                        }
                        onEditClick={() =>
                          navigate(`/files/zips/${file.zip_id}`)
                        }
                        onDeleteClick={() => handleDeleteFile(file.id)}
                      />
                    ))}
                  </div>
                )}
              </div>
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
};
