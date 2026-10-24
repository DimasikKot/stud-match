import { useState, useEffect } from "react";
import toast from "react-hot-toast";

import { TextUI } from "@/shared/components/TextUI";
import { TextField } from "@/shared/components/TextField";
import { FileCard } from "@/shared/components/FileCard";
import type { JsonValue } from "@/shared/api/model";
import { fetchFiles, type FileListResponse } from "@/shared/api/file";
import { CheckboxUI } from "@/shared/components/CheckboxUI";

const BASE_MODELS: string[] = JSON.parse(
  import.meta.env.VITE_BASE_MODELS || "[]",
);

const CLEAR_PARAMETERS: Record<string, JsonValue> = JSON.parse(
  import.meta.env.VITE_CLEAR_PARAMETERS || "{}",
);

export const ModelSettings = ({
  projectId,
  setIsLoading,
  editParams,
  setEditParams,
  trainingFilesIds,
  setTrainingFilesIds,
  predictionFilesIds,
  setPredictionFilesIds,
}: {
  projectId: number | string;
  setIsLoading: (value: React.SetStateAction<boolean>) => void;
  editParams: string;
  setEditParams: (value: React.SetStateAction<string>) => void;
  trainingFilesIds: number[];
  setTrainingFilesIds: (value: React.SetStateAction<number[]>) => void;
  predictionFilesIds: number[];
  setPredictionFilesIds: (value: React.SetStateAction<number[]>) => void;
}) => {
  const [files, setFiles] = useState<FileListResponse[]>([]);

  const [searchTraining, setSearchTraining] = useState("");
  const filteredTrainingFiles = files.filter((file) =>
    file.name.toLowerCase().includes(searchTraining.toLowerCase()),
  );

  const [searchPrediction, setSearchPrediction] = useState("");
  const filteredPredictionFiles = files.filter((file) =>
    file.name.toLowerCase().includes(searchPrediction.toLowerCase()),
  );

  useEffect(() => {
    const loadFiles = async () => {
      setIsLoading(true);
      const response = await fetchFiles(projectId);
      setIsLoading(false);

      if (response) {
        setFiles(response.data);
      }
    };

    loadFiles();
  }, [projectId, setIsLoading]);

  const changeBaseModel = async (model: string) => {
    try {
      const parsed = JSON.parse(editParams || "{}");

      parsed["Базовая модель"] = model;

      setEditParams(JSON.stringify(parsed, null, 2));
    } catch {
      toast.error("Некорректный JSON");
    }
  };

  const toggleFile = (id: number, type: "training" | "for_prediction") => {
    const setter =
      type === "training" ? setTrainingFilesIds : setPredictionFilesIds;
    const current = type === "training" ? trainingFilesIds : predictionFilesIds;

    if (current.includes(id)) {
      setter(current.filter((i) => i !== id));
    } else {
      setter([...current, id]);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <div>
        <TextUI variant="title">Выбор базовой модели</TextUI>

        <div
          style={{
            display: "flex",
            gap: 8,
            flexWrap: "wrap",
            marginBottom: 12,
          }}
        >
          {BASE_MODELS.map((model) => {
            let isActive = false;

            try {
              const parsed = JSON.parse(editParams || "{}");
              isActive = parsed["Базовая модель"] === model;
            } catch {
              console.error("Некорректный JSON");
            }

            return (
              <button
                key={model}
                type="button"
                onClick={() => changeBaseModel(model)}
                className={`
                px-3 py-1.5 rounded-lg border transition-all duration-200 
                ${
                  isActive
                    ? "bg-blue-500 text-white border-blue-500 shadow-md"
                    : "bg-white text-gray-700 border-gray-300 hover:bg-gray-100"
                }
                `}
              >
                {model}
              </button>
            );
          })}
        </div>
      </div>

      <div>
        <TextUI variant="title">Параметры обучения</TextUI>

        <TextField
          isArea
          rows={10}
          value={editParams}
          onChange={(e) => setEditParams(e.target.value)}
          placeholder={JSON.stringify(CLEAR_PARAMETERS, null, 2)}
        />
      </div>

      <div className="flex flex-col gap-4">
        <div className="flex flex-col lg:flex-row items-center justify-between gap-4">
          <TextUI variant="title" className="mb-2">
            Выбор файлов, на которых будет обучаться модель
          </TextUI>

          <TextField
            name="searchFile"
            value={searchTraining}
            setValue={setSearchTraining}
            placeholder="Поиск по имени файла..."
            className="max-w-md h-fit"
          />
        </div>

        <div className="h-80 border border-gray-300 rounded-2xl bg-white overflow-clip">
          {filteredTrainingFiles.length === 0 && (
            <TextUI variant="desc" className="text-center w-full mt-6">
              {searchTraining
                ? "Файлы по запросу не найдены"
                : "В проекте пока нет файлов"}
            </TextUI>
          )}

          <div className="grid grid-cols-2 md:grid-cols-3 h-full overflow-y-auto gap-2 p-3">
            {filteredTrainingFiles.map((file) => (
              <div
                key={file.id}
                className="flex items-start gap-2 p-2 w-full h-fit hover:bg-gray-100 rounded-xl cursor-pointer transition-colors"
                onClick={() => toggleFile(file.id, "training")}
              >
                <CheckboxUI
                  value={trainingFilesIds.includes(file.id)}
                  onClick={() => {}}
                />
                <FileCard file={file} variant="compact" className="h-fit" />
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-4">
        <div className="flex flex-col lg:flex-row items-center justify-between gap-4">
          <TextUI variant="title">
            Выбор файлов, которые будут размечены моделью
          </TextUI>

          <TextField
            name="searchFile"
            value={searchPrediction}
            setValue={setSearchPrediction}
            placeholder="Поиск по имени файла..."
            className="max-w-md h-fit"
          />
        </div>

        <div className="h-80 border border-gray-300 rounded-2xl bg-white overflow-clip">
          {filteredPredictionFiles.length === 0 && (
            <TextUI variant="desc" className="text-center w-full mt-6">
              {searchTraining
                ? "Файлы по запросу не найдены"
                : "В проекте пока нет файлов"}
            </TextUI>
          )}

          <div className="grid grid-cols-2 md:grid-cols-3 gap-2 h-full overflow-y-auto p-3">
            {filteredPredictionFiles.map((file) => (
              <div
                key={file.id}
                className="flex items-start gap-2 p-2 h-fit w-full hover:bg-gray-100 rounded-xl cursor-pointer transition-colors"
                onClick={() => toggleFile(file.id, "for_prediction")}
              >
                <CheckboxUI
                  value={predictionFilesIds.includes(file.id)}
                  onClick={() => {}}
                />
                <FileCard file={file} variant="compact" className="h-fit" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
