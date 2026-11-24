import { useEffect, useRef, useState } from "react";
import toast from "react-hot-toast";

import { ButtonUI } from "@/shared/components/UI/ButtonUI";
import { TextUI } from "@/shared/components/UI/TextUI";
import { FileCard } from "@/shared/components/FileCard";
import {
  deleteFile,
  fetchFiles,
  fileDownloadUrl,
  fileViewUrl,
  uploadFiles,
  type FileResponse,
} from "@/shared/api/file";
import { IconUI } from "@/shared/components/UI/IconUI";
import { PageLayout } from "@/shared/components/Layouts/PageLayout";

const formatSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} Б`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} КБ`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} МБ`;
};

export function Files() {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [files, setFiles] = useState<FileResponse[]>([]);
  const [selected, setSelected] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const loadFiles = () =>
    fetchFiles()
      .then((response) => setFiles(response.data))
      .catch(() => {});

  useEffect(() => {
    loadFiles();
  }, []);

  const handleSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const picked = Array.from(e.target.files ?? []);
    if (picked.length > 0) {
      setSelected((prev) => [...prev, ...picked]);
    }
    e.target.value = "";
  };

  const removeSelected = (index: number) =>
    setSelected((prev) => prev.filter((_, i) => i !== index));

  const handleUpload = async () => {
    if (selected.length === 0) {
      toast.error("Выберите хотя бы один файл");
      return;
    }
    setIsUploading(true);
    try {
      const uploaded = await uploadFiles(selected);
      toast.success(
        uploaded.length === 1
          ? "Файл загружен"
          : `Загружено файлов: ${uploaded.length}`,
      );
      setSelected([]);
      await loadFiles();
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (file: FileResponse) => {
    try {
      setFiles((prev) => prev.filter((f) => f.id !== file.id));
      await deleteFile(file.id);
      toast.success(`Файл "${file.name}" удалён`);
    } catch {
      setFiles((prev) => [...prev, file]);
      toast.error("Не удалось удалить файл");
    }
  };

  return (
    <PageLayout title="Файлы студентов">
      <div className="bg-white border border-gray-300 p-6">
        <TextUI variant="title" className="mb-4">
          Загрузка файлов
        </TextUI>

        <input
          ref={fileInputRef}
          type="file"
          multiple
          className="hidden"
          onChange={handleSelect}
        />

        <button
          onClick={() => fileInputRef.current?.click()}
          className="w-full border-2 border-dashed border-gray-300 hover:border-blue-400
              p-8 flex flex-col items-center gap-2 text-gray-500
              hover:text-blue-600 transition-colors cursor-pointer"
        >
          <IconUI size="32px" name="cloud_upload" />
          <TextUI variant="normal">Нажмите, чтобы выбрать файлы</TextUI>
          <TextUI variant="desc">Можно выбрать несколько файлов сразу</TextUI>
        </button>

        {selected.length > 0 && (
          <div className="mt-4">
            <div className="mt-4 flex gap-3">
              <ButtonUI onClick={handleUpload} disabled={isUploading}>
                {isUploading ? "Загрузка..." : "Загрузить"}
              </ButtonUI>

              <ButtonUI
                variant="secondary"
                onClick={() => setSelected([])}
                disabled={isUploading}
              >
                Очистить
              </ButtonUI>
            </div>

            <TextUI variant="label" className="mt-4">
              Выбрано файлов: {selected.length}
            </TextUI>

            <div className="flex flex-col gap-2 mt-4">
              {selected.map((file, index) => (
                <div
                  key={`${file.name}-${index}`}
                  className="flex items-center justify-between gap-3
                      bg-gray-50 border border-gray-200 px-4 py-2"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <IconUI size="20px" name="description" color="gray-400" />
                    <TextUI variant="normal" className="line-clamp-1">
                      {file.name}
                    </TextUI>
                    <TextUI variant="desc" span>
                      {formatSize(file.size)}
                    </TextUI>
                  </div>
                  <ButtonUI
                    variant="icon"
                    onClick={() => removeSelected(index)}
                    className="text-red-600 hover:text-red-800"
                  >
                    <IconUI size="20px" name="close" />
                  </ButtonUI>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Список файлов */}
      <div className="mt-8">
        <TextUI variant="header" className="mb-4">
          Загруженные файлы ({files.length})
        </TextUI>

        {files.length === 0 ? (
          <div className="bg-white border border-gray-300 text-center h-full">
            <TextUI variant="desc">Файлов пока нет</TextUI>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {files.map((file) => (
              <FileCard
                key={file.id}
                file={file}
                onClick={() => window.open(fileViewUrl(file.id), "_blank")}
                onDownloadClick={() =>
                  window.open(fileDownloadUrl(file.id), "_blank")
                }
                onDeleteClick={() => handleDelete(file)}
              />
            ))}
          </div>
        )}
      </div>
    </PageLayout>
  );
}
