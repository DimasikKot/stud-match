import type { ZipResponse } from "@/shared/api/zips";
import { TextUI } from "@/shared/components/UI/TextUI";
import { ButtonUI } from "./UI/ButtonUI";
import { IconUI } from "./UI/IconUI";

const STATUS_ICONS: Record<string, { name: string; className: string }> = {
  completed: { name: "check_circle", className: "text-green-500" },
  failed: { name: "error", className: "text-red-500" },
  processing: { name: "hourglass_top", className: "text-yellow-500" },
  pending: { name: "hourglass_empty", className: "text-gray-500" },
};

export const ZipCard = ({
  zip,
  onClick,
  onDeleteClick,
}: {
  zip: ZipResponse;
  onClick?: () => void;
  onDeleteClick?: React.MouseEventHandler<HTMLButtonElement>;
}) => {
  const statusIcon = STATUS_ICONS[zip.status] ?? STATUS_ICONS.pending;

  return (
    <div
      onClick={onClick}
      className="flex flex-col justify-between pb-2 px-1 gap-1 overflow-clip
        transition-all duration-200 cursor-pointer
        bg-white border border-gray-300 hover:border-gray-400 hover:shadow-md"
    >
      <div className="flex-1 h-full">
        <div className="flex flex-row justify-between gap-4">
          <div className="flex flex-1 min-w-0 max-h-12 flex-row items-center gap-2">
            <TextUI
              variant="title"
              title={zip.name}
              className="-mt-1 line-clamp-1"
            >
              {zip.name}
            </TextUI>
          </div>

          <IconUI name={statusIcon.name} className={statusIcon.className} />
        </div>
      </div>

      <div className="w-full flex-1 border-b border-gray-300" />

      <div className="flex justify-between -mb-1 gap-3 items-center">
        <TextUI variant="desc" className="flex-1 text-center">
          Файлов: {zip.files_count}
        </TextUI>

        <TextUI
          variant="desc"
          className="flex-1 text-center"
          title={new Date(zip.date).toLocaleString("ru-RU")}
        >
          {new Date(zip.date).toLocaleDateString("ru-RU")}
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
