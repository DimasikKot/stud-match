import toast from "react-hot-toast";

import type { ModelListResponse } from "@/shared/api/model";
import { TextUI } from "@/shared/components/TextUI";
import { ButtonUI } from "./ButtonUI";

export const ModelCard = ({
  model,
  onClick,
  onEditClick = () => toast.error("Обработка редактирования не настроена"),
  onCopyClick = () => toast.error("Обработка копирования не настроена"),
  onDownloadClick = () => toast.error("Обработка скачивания не настроена"),
  onStopClick = () => toast.error("Обработка остановки не настроена"),
  onDeleteClick = () => toast.error("Обработка удаления не настроена"),
  dateIsCreatedAt = false,
  className = "",
  variant = "normal",
}: {
  model: ModelListResponse;
  onClick?: () => void;
  onEditClick?: React.MouseEventHandler<HTMLButtonElement>;
  onCopyClick?: React.MouseEventHandler<HTMLButtonElement>;
  onDownloadClick?: React.MouseEventHandler<HTMLButtonElement>;
  onStopClick?: React.MouseEventHandler<HTMLButtonElement>;
  onDeleteClick?: React.MouseEventHandler<HTMLButtonElement>;
  dateIsCreatedAt?: boolean;
  className?: string;
  variant?: "normal" | "compact";
}) => {
  const date = dateIsCreatedAt ? model.created_at : model.updated_at;

  return (
    <div
      onClick={onClick}
      className={`
        bg-white border border-gray-300 rounded-2xl p-4 gap-3
        ${variant === "normal" && "hover:border-gray-400 hover:shadow-md"} transition-all duration-200
        cursor-pointer flex flex-col justify-between w-full
        ${className}
      `}
    >
      <div className="flex-1 h-full">
        <div className="flex flex-row justify-between gap-4">
          <div className="flex w-full flex-row gap-2">
            <TextUI variant="title" maxLines={1} className="-mt-1">
              {model.name}
              {/* {model.parameters["Базовая модель"] && (
                  <> ({String(model.parameters["Базовая модель"])})</>
                )} */}
            </TextUI>

            {model.parameters["Базовая модель"] && (
              <TextUI
                variant="label"
                className="mt-0.75 h-min w-40 line-clamp-1" // text-orange-400
              >
                {String(model.parameters["Базовая модель"]).split("/").pop()}
              </TextUI>
            )}

            {/* <TextUI
                variant="desc"
                className="flex items-end mt-0.5 h-min w-26"
              >
                (id: {model.id})
              </TextUI> */}
          </div>

          {3 <= model.progress && model.progress <= 99 && (
            <TextUI variant="normal" className="text-cyan-500 -mr-3">
              {`${model.progress}%`}
            </TextUI>
          )}

          {101 <= model.progress && model.progress <= 199 && (
            <TextUI variant="normal" className="text-cyan-500 -mr-3">
              {`${model.progress - 100}%`}
            </TextUI>
          )}

          <div
            className={`flex items-center justify-center select-none material-icons
                ${
                  0 <= model.progress && model.progress <= 2
                    ? "text-amber-500"
                    : (3 <= model.progress && model.progress <= 99) ||
                        (101 <= model.progress && model.progress <= 199)
                      ? "text-cyan-500"
                      : "text-emerald-500"
                }`}
          >
            {model.progress === 0
              ? "edit_note"
              : 1 <= model.progress && model.progress <= 99
                ? "model_training"
                : 101 <= model.progress && model.progress <= 199
                  ? "edit_note"
                  : "school"}
            {/* task_alt */}
          </div>

          {variant === "normal" &&
            model.progress >= 2 &&
            model.progress <= 99 && (
              <div className="-ml-3">
                <ButtonUI
                  onClick={onStopClick}
                  variant="icon"
                  className="flex-max text-right text-red-600 hover:text-red-800"
                >
                  <div className="select-none material-icons">cancel</div>
                </ButtonUI>
              </div>
            )}
        </div>

        <div className="flex flex-col overflow-auto">
          {model.training_files.length > 0 && (
            <TextUI variant="label">
              Файлы для обучения:{" "}
              <TextUI isSpan variant="desc">
                {model.training_files.map((file) => file.name).join(" , ")}
              </TextUI>
            </TextUI>
          )}

          {model.prediction_files.length > 0 && (
            <TextUI variant="label">
              Будут размечены:{" "}
              <TextUI isSpan variant="desc">
                {model.prediction_files.map((file) => file.name).join(" , ")}
              </TextUI>
            </TextUI>
          )}

          {model.predicted_files.length > 0 && (
            <TextUI variant="label">
              Были размечены:{" "}
              <TextUI isSpan variant="desc">
                {model.predicted_files.map((file) => file.name).join(" , ")}
              </TextUI>
            </TextUI>
          )}

          <div className="mt-1 flex max-h-[20vh]">
            {Object.entries(model.parameters).length > 0 && (
              <div className="flex-1 w-[50%]">
                {Object.entries(model.parameters).map(([k, v]) => (
                  <div
                    key={k}
                    className="flex justify-between px-1 border-b border-orange-200"
                  >
                    <TextUI
                      variant="label"
                      className="text-orange-400 w-[45%] overflow-hidden"
                      maxLines={1}
                    >
                      {k}
                    </TextUI>

                    <TextUI
                      variant="desc"
                      className="text-orange-400 w-[50%] overflow-hidden"
                      isSpan
                      maxLines={1}
                    >
                      {String(v)}
                    </TextUI>
                  </div>
                ))}
              </div>
            )}

            {Object.entries(model.metrics).length > 0 && (
              <div className="flex-1 w-[50%]">
                {Object.entries(model.metrics).map(([k, v]) => (
                  <div
                    key={k}
                    className="flex justify-between px-1 border-b border-emerald-300"
                  >
                    <TextUI
                      variant="label"
                      className="text-green-500/90 w-[45%] overflow-hidden"
                      maxLines={1}
                    >
                      {k}
                    </TextUI>

                    <TextUI
                      variant="desc"
                      className="text-green-500/90 w-[50%] overflow-hidden"
                      isSpan
                      maxLines={1}
                    >
                      {String(v)}
                    </TextUI>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {variant === "normal" && (
        <>
          <div className="w-full flex-1 border-b border-gray-300" />

          <div className="flex justify-between -mb-1 gap-3">
            <div className="flex flex-max gap-3">
              <ButtonUI
                onClick={onEditClick}
                variant="icon"
                className="text-left"
              >
                <div className="select-none material-icons">edit</div>
              </ButtonUI>

              <ButtonUI
                onClick={(event) => onCopyClick?.(event)}
                variant="icon"
              >
                <div className="select-none material-icons">copy_all</div>
              </ButtonUI>

              {/* {Object.keys(model.metrics).length > 0 && (
                <ButtonUI onClick={() => setIsOpen(true)} variant="secondary">
                  <div className="select-none material-icons">insert_chart</div>
                </ButtonUI>
              )} */}

              <ButtonUI onClick={onDownloadClick} variant="icon">
                <div className="select-none material-icons">download</div>
              </ButtonUI>
            </div>

            <TextUI
              variant="desc"
              className="flex flex-1 text-center justify-center items-center"
            >
              {new Date(date).toLocaleDateString("ru-RU", {
                month: "long",
                day: "numeric",
                hour: "numeric",
                minute: "numeric",
              })}
            </TextUI>

            <div className="ml-18">
              <ButtonUI
                onClick={onDeleteClick}
                variant="icon"
                className="flex-max text-right text-red-600 hover:text-red-800"
              >
                <div
                  // className={`${Object.keys(model.metrics).length > 0 ? "ml-15" : "ml-9"} select-none material-icons`}
                  className="select-none material-icons"
                >
                  delete
                </div>
              </ButtonUI>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
