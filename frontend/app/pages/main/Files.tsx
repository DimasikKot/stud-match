import { useEffect, useRef, useState } from "react";
import toast from "react-hot-toast";

import { Header } from "@/shared/components/Header";
import { ButtonPage } from "@/shared/components/ButtonPage";
import { ButtonUI } from "@/shared/components/ButtonUI";
import { TextUI } from "@/shared/components/TextUI";
import { FileCard } from "@/shared/components/FileCard";
import {
  deleteFile,
  fetchFiles,
  fileDownloadUrl,
  fileViewUrl,
  uploadFiles,
  type FileListResponse,
} from "@/shared/api/file";

const formatSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} Б`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} КБ`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} МБ`;
};

export function Files() {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [files, setFiles] = useState<FileListResponse[]>([]);
  const [selected, setSelected] = useState<File[]>([]);
  const [isLoading, setIsLoading] = useState(false);
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

  const handleDelete = async (file: FileListResponse) => {
    setIsLoading(true);
    try {
      await deleteFile(file.id);
      toast.success(`Файл "${file.name}" удалён`);
      await loadFiles();
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Header title="Файлы" />

      <div className="max-w-6xl mx-auto m-6 mb-20 w-full">
        <ButtonPage
          onClick={() => window.scrollTo({ top: 0 })}
          isLoading={isLoading}
        />

        {/* Загрузка файлов */}
        <div className="bg-white border border-gray-300 rounded-3xl p-6">
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
              rounded-2xl p-8 flex flex-col items-center gap-2 text-gray-500
              hover:text-blue-600 transition-colors cursor-pointer"
          >
            <span className="material-icons text-4xl">cloud_upload</span>
            <TextUI variant="normal">Нажмите, чтобы выбрать файлы</TextUI>
            <TextUI variant="desc">Можно выбрать несколько файлов сразу</TextUI>
          </button>

          {selected.length > 0 && (
            <div className="mt-4">
              <TextUI variant="label" className="mb-2">
                Выбрано файлов: {selected.length}
              </TextUI>
              <div className="flex flex-col gap-2">
                {selected.map((file, index) => (
                  <div
                    key={`${file.name}-${index}`}
                    className="flex items-center justify-between gap-3
                      bg-gray-50 border border-gray-200 rounded-xl px-4 py-2"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <span className="material-icons text-gray-400">
                        description
                      </span>
                      <TextUI variant="normal" maxLines={1}>
                        {file.name}
                      </TextUI>
                      <TextUI variant="desc" isSpan>
                        {formatSize(file.size)}
                      </TextUI>
                    </div>
                    <ButtonUI
                      variant="icon"
                      onClick={() => removeSelected(index)}
                      className="text-red-600 hover:text-red-800"
                    >
                      <span className="material-icons">close</span>
                    </ButtonUI>
                  </div>
                ))}
              </div>

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
            </div>
          )}
        </div>

        {/* Список файлов */}
        <div className="mt-8">
          <TextUI variant="header" className="mb-4">
            Загруженные файлы ({files.length})
          </TextUI>

          {files.length === 0 ? (
            <div className="bg-white border border-gray-300 rounded-3xl p-8 text-center">
              <TextUI variant="desc">Файлов пока нет</TextUI>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {files.map((file) => (
                <FileCard
                  key={file.id}
                  file={file}
                  dateIsCreatedAt
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
      </div>
    </div>
  );
}
