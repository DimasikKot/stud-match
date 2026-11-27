import { useNavigate } from "react-router-dom";

import type { StudentDetailResponse } from "@/shared/api/students";
import { fileDownloadUrl, fileViewUrl } from "@/shared/api/file";
import { TextUI } from "@/shared/components/UI/TextUI";
import { ButtonUI } from "./UI/ButtonUI";
import { IconUI } from "./UI/IconUI";

const FILE_STATUS_LABELS: Record<string, string> = {
  not_extracted: "Не извлечено",
  queued: "В очереди",
  extracting: "Извлечение",
  extracted: "Извлечено",
  applied: "Применено",
  failed: "Ошибка",
  deleted_from_rustfs: "Удалён из хранилища",
};

const formatSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} Б`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} КБ`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} МБ`;
};

export const StudentDetailsModal = ({
  student,
  isLoading,
  hasError,
  onClose,
}: {
  student: StudentDetailResponse | null;
  isLoading: boolean;
  hasError: boolean;
  onClose: () => void;
}) => {
  const navigate = useNavigate();

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white border border-gray-300 w-full max-w-2xl max-h-[85vh]
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
                    font-mono whitespace-pre-wrap break-words max-h-64 overflow-y-auto"
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
                  <div className="flex flex-col gap-2">
                    {student.files.map((file) => (
                      <div
                        key={file.id}
                        className="flex items-center justify-between gap-3
                          bg-gray-50 border border-gray-200 px-4 py-2"
                      >
                        <div className="flex-1 min-w-0">
                          <TextUI
                            variant="normal"
                            title={file.name}
                            className="line-clamp-1"
                          >
                            {file.name}
                          </TextUI>
                          <TextUI variant="desc">
                            {formatSize(file.size)} ·{" "}
                            {FILE_STATUS_LABELS[file.status] ?? file.status}
                          </TextUI>
                        </div>

                        <div className="flex items-center gap-1 shrink-0">
                          <ButtonUI
                            variant="icon"
                            title="Открыть"
                            onClick={() =>
                              window.open(fileViewUrl(file.id), "_blank")
                            }
                          >
                            <IconUI size="20px" name="visibility" />
                          </ButtonUI>
                          <ButtonUI
                            variant="icon"
                            title="Скачать"
                            onClick={() =>
                              window.open(fileDownloadUrl(file.id), "_blank")
                            }
                          >
                            <IconUI size="20px" name="download" />
                          </ButtonUI>
                          <ButtonUI
                            variant="icon"
                            title="Открыть архив"
                            onClick={() =>
                              navigate(`/files/zips/${file.zip_id}`)
                            }
                          >
                            <IconUI size="20px" name="folder_zip" />
                          </ButtonUI>
                        </div>
                      </div>
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
