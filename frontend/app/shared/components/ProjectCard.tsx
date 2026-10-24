import toast from "react-hot-toast";

import type { ProjectDbResponse } from "@/shared/api/projects";
import { TextUI } from "@/shared/components/TextUI";
import { ButtonUI } from "@/shared/components/ButtonUI";

export const ProjectCard = ({
  project,
  onClick,
  onEditClick = () => toast.error("Обработка редактирования не настроена"),
  onDeleteClick = () => toast.error("Обработка удаления не настроена"),
  dateIsCreatedAt = false,
  className = "",
}: {
  project: ProjectDbResponse;
  onClick?: () => void;
  onEditClick?: React.MouseEventHandler<HTMLButtonElement>;
  onDeleteClick?: React.MouseEventHandler<HTMLButtonElement>;
  dateIsCreatedAt?: boolean;
  className?: string;
}) => {
  const date = dateIsCreatedAt ? project.created_at : project.updated_at;

  return (
    <div
      onClick={onClick}
      className={`
        bg-white border border-gray-300 rounded-2xl p-4 gap-3
        hover:border-gray-400 hover:shadow-md transition-all duration-200
        cursor-pointer flex flex-col justify-between w-full
        ${className}
      `}
    >
      <div className="flex-1 h-full">
        <div className="flex flex-row justify-between gap-4">
          <div className="flex w-full flex-row gap-2">
            <TextUI variant="title" maxLines={1} className="-mt-1">
              {project.name}
            </TextUI>

            {/* <TextUI variant="desc" className="flex items-end mt-0.5 h-min w-26">
              (id: {project.id})
            </TextUI> */}
          </div>

          <div className="flex items-center justify-center select-none material-icons">
            {project.is_public ? "public" : "lock"}
          </div>
        </div>

        {project.description && (
          <TextUI variant="desc" maxLines={2} className="mt-1">
            {project.description}
          </TextUI>
        )}
      </div>

      <div className="w-full flex-1 border-b border-gray-300" />

      <div className="flex justify-between -mb-1 gap-3">
        <ButtonUI
          onClick={onEditClick}
          variant="icon"
          className="flex-max text-left"
        >
          <div className="select-none material-icons">edit</div>
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

        <ButtonUI
          onClick={onDeleteClick}
          variant="icon"
          className="flex-max text-right text-red-600 hover:text-red-800"
        >
          <div className="select-none material-icons">delete</div>
        </ButtonUI>
      </div>
    </div>
  );
};
