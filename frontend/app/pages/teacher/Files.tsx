import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";

import { ButtonUI } from "@/shared/components/UI/ButtonUI";
import { TextUI } from "@/shared/components/UI/TextUI";
import { TooltipUI } from "@/shared/components/UI/TooltipUI";
import { ZipCard } from "@/shared/components/ZipCard";
import { IconUI } from "@/shared/components/UI/IconUI";
import { PageLayout } from "@/shared/components/Layouts/PageLayout";
import { uploadFiles } from "@/shared/api/file";
import {
  extractFeatures,
  fetchRustfsObjects,
  RustfsObjectStatus,
  type RustfsObjectStatusValue,
  type RustfsObjectsResponse,
} from "@/shared/api/rustfsObjects";
import {
  fetchKafkaTopicMessages,
  type GetHealthResponse,
} from "@/shared/api/healths";
import { deleteZip, fetchZips, type ZipResponse } from "@/shared/api/zips";

const STATUS_LABELS: Record<RustfsObjectStatusValue, string> = {
  [RustfsObjectStatus.NotExtracted]: "Не извлечено",
  [RustfsObjectStatus.Failed]: "Ошибки",
  [RustfsObjectStatus.Queued]: "В очереди",
  [RustfsObjectStatus.Extracting]: "Извлечение",
  [RustfsObjectStatus.Extracted]: "Извлечено",
};

const KAFKA_TOPICS = [
  { name: "features.tasks", label: "Задачи извлечения признаков" },
  { name: "features.results", label: "Результаты извлечения признаков" },
  { name: "distribution.tasks", label: "Задачи распределения" },
  { name: "distribution.results", label: "Результаты распределения" },
] as const;

const formatSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} Б`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} КБ`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} МБ`;
};

export function Files() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [zips, setZips] = useState<ZipResponse[]>([]);
  const [rustfsObjects, setRustfsObjects] = useState<
    Partial<Record<RustfsObjectStatusValue, RustfsObjectsResponse>>
  >({});
  const [kafkaTopics, setKafkaTopics] = useState<
    Partial<Record<string, GetHealthResponse | undefined>>
  >({});
  const [selected, setSelected] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<Record<number, number>>(
    {},
  );

  const loadZips = () =>
    fetchZips()
      .then((response) => setZips(response.data))
      .catch(() => {});

  const loadRustfsObjects = () => {
    const statuses = Object.values(RustfsObjectStatus);
    Promise.all(
      statuses.map(
        async (status) => [status, await fetchRustfsObjects(status)] as const,
      ),
    ).then((entries) => {
      setRustfsObjects(
        Object.fromEntries(
          entries.filter(([, response]) => response !== undefined),
        ) as Partial<Record<RustfsObjectStatusValue, RustfsObjectsResponse>>,
      );
    });
  };

  const loadKafkaTopics = () => {
    Promise.all(
      KAFKA_TOPICS.map(
        async (topic) =>
          [topic.name, await fetchKafkaTopicMessages(topic.name)] as const,
      ),
    ).then((entries) => {
      setKafkaTopics(Object.fromEntries(entries));
    });
  };

  useEffect(() => {
    loadZips();
    loadRustfsObjects();
    loadKafkaTopics();
  }, []);

  const handleExtractFeatures = async (
    status: RustfsObjectStatusValue = RustfsObjectStatus.NotExtracted,
  ) => {
    setIsExtracting(true);
    try {
      const response = await extractFeatures(status);
      if (response) {
        toast.success(response.detail);
      }
      loadRustfsObjects();
      loadKafkaTopics();
    } finally {
      setIsExtracting(false);
    }
  };

  const handleSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const picked = Array.from(e.target.files ?? []);
    const archives = picked.filter((file) =>
      file.name.toLowerCase().endsWith(".zip"),
    );
    if (archives.length < picked.length) {
      toast.error("Можно загружать только zip-архивы");
    }
    if (archives.length > 0) {
      setSelected((prev) => [...prev, ...archives]);
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
    setUploadProgress({});
    try {
      const uploaded = await uploadFiles(selected, (index, progress) =>
        setUploadProgress((prev) => ({ ...prev, [index]: progress })),
      );
      toast.success(
        uploaded.length === 1
          ? "Архив принят в обработку"
          : `Архивов принято в обработку: ${uploaded.length}`,
      );
      setSelected([]);
      setUploadProgress({});
      await loadZips();
    } finally {
      setIsUploading(false);
    }
  };

  const handleDeleteZip = async (zip: ZipResponse) => {
    try {
      setZips((prev) => prev.filter((z) => z.id !== zip.id));
      await deleteZip(zip.id);
      toast.success(`Архив "${zip.name}" удалён`);
    } catch {
      setZips((prev) => [...prev, zip]);
      toast.error("Не удалось удалить архив");
    }
  };

  return (
    <PageLayout title="Файлы студентов">
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 mb-8">
        {Object.values(RustfsObjectStatus).map((status) => {
          const response = rustfsObjects[status];
          return (
            <TooltipUI
              key={status}
              content={
                response
                  ? (response as unknown as Record<string, unknown>)
                  : undefined
              }
              isJSON
              placement="bottom"
            >
              <div className="bg-white border border-gray-300 p-4">
                <TextUI variant="label">{STATUS_LABELS[status]}</TextUI>
                <TextUI variant="header">
                  {response ? response.count : "..."}
                </TextUI>
                {status === RustfsObjectStatus.NotExtracted && (
                  <ButtonUI
                    className="mt-3 w-full"
                    onClick={() => handleExtractFeatures()}
                    disabled={isExtracting}
                  >
                    {isExtracting ? "Отправка..." : "Начать извлечение"}
                  </ButtonUI>
                )}
                {status === RustfsObjectStatus.Failed && (
                  <ButtonUI
                    className="mt-3 w-full"
                    onClick={() =>
                      handleExtractFeatures(RustfsObjectStatus.Failed)
                    }
                    disabled={isExtracting}
                  >
                    {isExtracting ? "Отправка..." : "Повторить извлечение"}
                  </ButtonUI>
                )}
              </div>
            </TooltipUI>
          );
        })}
      </div>

      <div className="mt-8">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <TextUI variant="header">Очереди Kafka</TextUI>

          <ButtonUI variant="secondary" onClick={loadKafkaTopics}>
            Обновить
          </ButtonUI>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {KAFKA_TOPICS.map((topic) => {
            const response = kafkaTopics[topic.name];
            const metrics = response?.metrics as
              { message_count?: number; group_lag?: number } | undefined;
            return (
              <TooltipUI
                key={topic.name}
                content={
                  response
                    ? (response as unknown as Record<string, unknown>)
                    : undefined
                }
                isJSON
                placement="bottom"
              >
                <div className="bg-white border border-gray-300 p-4">
                  <TextUI variant="label">{topic.label}</TextUI>
                  <TextUI variant="desc">{topic.name}</TextUI>
                  <TextUI variant="header">
                    {metrics?.message_count ?? "..."}
                  </TextUI>
                  <TextUI variant="desc">
                    сообщений, в очереди: {metrics?.group_lag ?? "..."}
                  </TextUI>
                </div>
              </TooltipUI>
            );
          })}
        </div>
      </div>

      <div className="bg-white border border-gray-300 p-6 mt-8">
        <TextUI variant="title" className="mb-4">
          Загрузка файлов
        </TextUI>

        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".zip,application/zip"
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
              {selected.map((file, index) => {
                const progress = uploadProgress[index] ?? 0;
                return (
                  <div
                    key={`${file.name}-${index}`}
                    className="relative flex items-center justify-between gap-3
                        bg-gray-50 border border-gray-200 px-4 py-2 overflow-hidden"
                  >
                    <div
                      className="absolute inset-y-0 left-0 bg-blue-200 transition-all"
                      style={{ width: `${progress}%` }}
                    />
                    <div className="relative flex items-center gap-3 min-w-0">
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
                      disabled={isUploading}
                      className="relative text-red-600 hover:text-red-800"
                    >
                      <IconUI size="20px" name="close" />
                    </ButtonUI>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      <div className="mt-8">
        <TextUI variant="header" className="mb-4">
          Загруженные архивы ({zips.length})
        </TextUI>

        {zips.length === 0 ? (
          <div className="bg-white border border-gray-300 text-center h-full">
            <TextUI variant="desc">Архивов пока нет</TextUI>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {zips.map((zip) => (
              <ZipCard
                key={zip.id}
                zip={zip}
                onClick={() => navigate(`/files/zips/${zip.id}`)}
                onDeleteClick={() => handleDeleteZip(zip)}
              />
            ))}
          </div>
        )}
      </div>
    </PageLayout>
  );
}
