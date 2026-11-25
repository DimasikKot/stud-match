import toast from "react-hot-toast";

import { TextUI } from "@/shared/components/UI/TextUI";
import { ButtonUI } from "./UI/ButtonUI";
import { IconUI } from "./UI/IconUI";

export interface FileCardFile {
  id: number;
  name: string;
  status: string;
  student_fullname: string | null;
}

export const FileCard = ({
  file,
  onClick,
  onEditClick = () => toast.error("Обработка редактирования не настроена"),
  onDownloadClick = () => toast.error("Обработка скачивания не настроена"),
  onDeleteClick = () => toast.error("Обработка удаления не настроена"),
  className: customClassName,
  variant = "normal",
}: {
  file: FileCardFile;
  onClick?: () => void;
  onEditClick?: React.MouseEventHandler<HTMLButtonElement>;
  onDownloadClick?: React.MouseEventHandler<HTMLButtonElement>;
  onDeleteClick?: React.MouseEventHandler<HTMLButtonElement>;
  className?: string;
  variant?: "normal" | "compact";
}) => {
  const className = `
        flex flex-col justify-between pb-2 px-1 gap-1 overflow-clip
        transition-all duration-200 cursor-pointer 
        bg-white border border-gray-300
        ${variant === "normal" && "hover:border-gray-400 hover:shadow-md"}
        ${customClassName}
      `;

  return (
    <div onClick={onClick} className={className}>
      <div className="flex-1 h-full">
        <div className="flex flex-row justify-between gap-4">
          <div className="flex flex-1 min-w-0 max-h-12 flex-row items-center gap-2">
            <TextUI
              variant="title"
              title={file.name}
              className="-mt-1 line-clamp-1"
            >
              {file.name}
            </TextUI>

            {/* <TextUI variant="desc" className="flex items-end mt-0.5 h-min shrink-0">
              (id: {file.id})
            </TextUI> */}
          </div>

          <IconUI
            name={file.status === "extracted" ? "sell" : "help_outline"}
            className={
              file.status === "extracted" ? "text-green-500" : "text-gray-500"
            }
          />
        </div>
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
              title={file.student_fullname ?? undefined}
              className="flex flex-1 text-center justify-center items-center line-clamp-1"
            >
              {file.student_fullname ?? "Студент не привязан"}
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
