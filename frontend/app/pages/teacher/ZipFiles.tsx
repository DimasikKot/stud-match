import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import toast from "react-hot-toast";

import { ButtonUI } from "@/shared/components/UI/ButtonUI";
import { TextUI } from "@/shared/components/UI/TextUI";
import { FileCard } from "@/shared/components/FileCard";
import { IconUI } from "@/shared/components/UI/IconUI";
import { PageLayout } from "@/shared/components/Layouts/PageLayout";
import { deleteFile, fileDownloadUrl, fileViewUrl } from "@/shared/api/file";
import { deleteZip, fetchZip, type ZipDetailResponse } from "@/shared/api/zips";

export function ZipFiles() {
  const { zipId } = useParams<{ zipId: string }>();
  const navigate = useNavigate();

  const [zip, setZip] = useState<ZipDetailResponse | null>(null);

  const loadZip = useCallback(() => {
    if (!zipId) return;
    fetchZip(Number(zipId))
      .then(setZip)
      .catch(() => navigate("/files"));
  }, [zipId, navigate]);

  useEffect(() => {
    loadZip();
  }, [loadZip]);

  const handleDeleteFile = async (fileId: number) => {
    try {
      setZip((prev) =>
        prev
          ? {
              ...prev,
              files: prev.files.filter((f) => f.id !== fileId),
              files_count: prev.files_count - 1,
            }
          : prev,
      );
      await deleteFile(fileId);
      toast.success("Файл удалён");
    } catch {
      loadZip();
      toast.error("Не удалось удалить файл");
    }
  };

  const handleDeleteZip = async () => {
    if (!zip) return;
    try {
      await deleteZip(zip.id);
      toast.success(`Архив "${zip.name}" удалён`);
      navigate("/files");
    } catch {
      toast.error("Не удалось удалить архив");
    }
  };

  return (
    <PageLayout title={zip ? `Архив: ${zip.name}` : "Архив"}>
      <ButtonUI
        variant="secondary"
        onClick={() => navigate("/files")}
        className="w-fit mb-4"
      >
        <span className="flex items-center gap-2">
          <IconUI size="20px" name="arrow_back" />
          Назад к архивам
        </span>
      </ButtonUI>

      {zip && (
        <div className="bg-white border border-gray-300 p-6">
          <div className="flex items-center justify-between gap-4">
            <div>
              <TextUI variant="title">{zip.name}</TextUI>
              <TextUI variant="desc" className="mt-1">
                Файлов: {zip.files_count} · Загружен:{" "}
                {new Date(zip.date).toLocaleString("ru-RU")}
              </TextUI>
            </div>

            <ButtonUI
              variant="secondary"
              onClick={handleDeleteZip}
              className="text-red-600"
            >
              Удалить архив
            </ButtonUI>
          </div>
        </div>
      )}

      <div className="mt-8">
        <TextUI variant="header" className="mb-4">
          Файлы ({zip?.files.length ?? 0})
        </TextUI>

        {!zip || zip.files.length === 0 ? (
          <div className="bg-white border border-gray-300 text-center">
            <TextUI variant="desc">
              {zip ? "В архиве нет файлов" : "Загрузка..."}
            </TextUI>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {zip.files.map((file) => (
              <FileCard
                key={file.id}
                file={file}
                onClick={() => window.open(fileViewUrl(file.id), "_blank")}
                onDownloadClick={() =>
                  window.open(fileDownloadUrl(file.id), "_blank")
                }
                onDeleteClick={() => handleDeleteFile(file.id)}
              />
            ))}
          </div>
        )}
      </div>
    </PageLayout>
  );
}
