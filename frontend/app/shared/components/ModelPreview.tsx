import { TextUI } from "@/shared/components/TextUI";
import type { ModelFullResponse } from "@/shared/api/model";
import { Link } from "react-router-dom";
import React from "react";

export const ModelPreview = ({
  model,
  projectId,
}: {
  model: ModelFullResponse;
  projectId: string;
}) => {
  return (
    <div
      className={`grid grid-cols-1 ${Object.entries(model.metrics).length > 0 ? "md:grid-cols-2" : ""} gap-8`}
    >
      {/* Параметры */}
      <div className="p-6 border border-orange-200 bg-orange-50/20 rounded-2xl">
        <TextUI variant="header" className="mb-4 text-orange-400" isSelectable>
          Параметры обучения
        </TextUI>

        <div className="space-y-2">
          {Object.entries(model.parameters).length > 0 &&
            Object.entries(model.parameters).map(([k, v]) => (
              <div
                key={k}
                className="flex justify-between py-1 border-b border-orange-200"
              >
                <TextUI
                  variant="subtitle"
                  className="text-orange-400 w-[45%] overflow-hidden"
                  isSelectable
                >
                  {k}
                </TextUI>

                <TextUI
                  className="text-orange-400 w-[50%] overflow-hidden"
                  isSpan
                  isSelectable
                >
                  {String(v)}
                </TextUI>
              </div>
            ))}
        </div>
      </div>

      {/* Метрики */}
      {Object.entries(model.metrics).length > 0 && (
        <div className="p-6 border border-emerald-300 bg-emerald-50/20 rounded-2xl">
          <TextUI
            variant="header"
            className="mb-4 text-emerald-500"
            isSelectable
          >
            Результаты обучения
          </TextUI>

          <div className="space-y-2">
            {Object.entries(model.metrics).map(([k, v]) => (
              <div
                key={k}
                className="flex justify-between py-1 border-b border-emerald-300"
              >
                <TextUI
                  variant="subtitle"
                  className="text-emerald-500 w-[45%] overflow-hidden"
                  isSelectable
                >
                  {k}
                </TextUI>

                <TextUI
                  className="text-emerald-500 w-[50%] overflow-hidden"
                  isSpan
                  isSelectable
                >
                  {String(v)}
                </TextUI>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Графики */}
      {Object.entries(model.graphs)
        .filter(([key]) => !key.includes("(описание)"))
        .map(([key, value]) => (
          <div key={key} className="border rounded-2xl p-3">
            <TextUI variant="subtitle" className="mb-2" isSelectable>
              {key}
            </TextUI>

            <img
              src={value}
              alt={key}
              className="w-full select-none rounded-lg"
            />

            {model.graphs[key + " (описание)"] && (
              <TextUI className="mt-2 whitespace-pre-line" isSelectable>
                {String(model.graphs[key + " (описание)"])}
              </TextUI>
            )}
          </div>
        ))}

      {/* Файлы */}
      <div className="flex flex-col p-6 border border-gray-300 rounded-2xl">
        <TextUI variant="title" isSelectable className="h-50%">
          Файлы, на которых будет обучаться:{" "}
          <TextUI variant="subtitle" isSpan isSelectable>
            {model.training_files.length > 0
              ? model.training_files.map((file, index) => (
                  <React.Fragment key={file.id}>
                    <TextUI variant="link" isSpan isSelectable>
                      <Link
                        to={`/projects/${projectId}/files/${file.id}`}
                        className="text-lg"
                      >
                        {file.name}
                      </Link>
                    </TextUI>

                    {index < model.training_files.length - 1 && ", "}
                  </React.Fragment>
                ))
              : "не выбраны"}
          </TextUI>
        </TextUI>

        <TextUI variant="title" isSelectable className="h-50%">
          Будут размечены:{" "}
          <TextUI variant="subtitle" isSpan isSelectable>
            {model.prediction_files.length > 0
              ? model.prediction_files.map((file, index) => (
                  <React.Fragment key={file.id}>
                    <TextUI variant="link" isSpan isSelectable>
                      <Link
                        to={`/projects/${projectId}/files/${file.id}`}
                        className="text-lg"
                      >
                        {file.name}
                      </Link>
                    </TextUI>

                    {index < model.prediction_files.length - 1 && ", "}
                  </React.Fragment>
                ))
              : "не выбраны"}
          </TextUI>
        </TextUI>

        {model.predicted_files.length > 0 && (
          <TextUI variant="title">
            Были размечены:{" "}
            <TextUI isSpan variant="subtitle">
              {model.predicted_files.map((file, index) => (
                <React.Fragment key={file.id}>
                  <TextUI variant="link" isSpan isSelectable>
                    <Link
                      to={`/projects/${projectId}/files/${file.id}`}
                      className="text-lg"
                    >
                      {file.name}
                    </Link>
                  </TextUI>

                  {index < model.predicted_files.length - 1 && ", "}
                </React.Fragment>
              ))}
            </TextUI>
          </TextUI>
        )}
      </div>
    </div>
  );
};
