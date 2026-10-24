import toast from "react-hot-toast";

import type { FileListResponse } from "@/shared/api/file";
import { TextUI } from "@/shared/components/TextUI";
import { ButtonUI } from "./ButtonUI";

export const FileCard = ({
  file,
  onClick,
  onEditClick = () => toast.error("Обработка редактирования не настроена"),
  onDownloadClick = () => toast.error("Обработка скачивания не настроена"),
  onDeleteClick = () => toast.error("Обработка удаления не настроена"),
  dateIsCreatedAt = false,
  className = "",
  variant = "normal",
}: {
  file: FileListResponse;
  onClick?: () => void;
  onEditClick?: React.MouseEventHandler<HTMLButtonElement>;
  onDownloadClick?: React.MouseEventHandler<HTMLButtonElement>;
  onDeleteClick?: React.MouseEventHandler<HTMLButtonElement>;
  dateIsCreatedAt?: boolean;
  className?: string;
  variant?: "normal" | "compact";
}) => {
  const date = dateIsCreatedAt ? file.created_at : file.updated_at;

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
              {file.name}
            </TextUI>

            {/* <TextUI variant="desc" className="flex items-end mt-0.5 h-min w-26">
              (id: {file.id})
            </TextUI> */}
          </div>

          <div
            className={`flex items-center justify-center select-none material-icons 
            ${file.is_labeled ? "text-green-500" : "text-gray-500"}`}
          >
            {file.is_labeled ? "sell" : "help_outline"}
          </div>
        </div>

        {file.total_rows && (
          <TextUI variant="desc" maxLines={1} className="mt-1">
            <strong>Строк:</strong> {file.total_rows}
          </TextUI>
        )}

        {file.prediction_model && (
          <TextUI variant="desc" maxLines={1} className="mt-1">
            <strong>Размечен моделью:</strong> {file.prediction_model.name}
            {" ("}
            {file.prediction_model.parameters["Базовая модель"] &&
              String(file.prediction_model.parameters["Базовая модель"])
                .split("/")
                .pop()}
            {")"}
          </TextUI>
        )}

        {file.origin_file && (
          <TextUI variant="desc" maxLines={1} className="mt-1">
            <strong>Исходный файл:</strong> {file.origin_file.name}
          </TextUI>
        )}
      </div>

      {variant === "normal" && (
        <>
          <div className="w-full flex-1 border-b border-gray-300" />

          <div className="flex justify-between -mb-1 gap-3">
            <ButtonUI
              onClick={onEditClick}
              variant="icon"
              className="flex-max text-left"
            >
              <div className="select-none material-icons">edit</div>
            </ButtonUI>

            <ButtonUI
              onClick={onDownloadClick}
              variant="icon"
              className="flex-max text-left"
            >
              <div className="select-none material-icons">download</div>
            </ButtonUI>

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

            <div className="ml-9">
              <ButtonUI
                onClick={onDeleteClick}
                variant="icon"
                className="flex-max text-right text-red-600 hover:text-red-800"
              >
                <div className="select-none material-icons">delete</div>
              </ButtonUI>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
