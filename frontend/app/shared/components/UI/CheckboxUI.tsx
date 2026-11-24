import { TextUI } from "./TextUI";

export const CheckboxUI = ({
  value,
  onClick,
  title,
  className,
}: {
  value: boolean;
  onClick: () => void;
  title?: string;
  className?: string;
}) => {
  return (
    <button
      type="button"
      onClick={onClick}
      // flex и items-center выравнивают иконку и текст в одну линию
      className={`flex items-center w-max cursor-pointer gap-2 p-2 ${title && "px-4"}  hover:bg-gray-200 rounded-full transition-colors ${className}`}
    >
      {/* Иконка из библиотеки Material Icons */}
      <span
        className={`material-icons select-none ${value ? "text-blue-600" : "text-gray-400"}`}
      >
        {value ? "check_box" : "check_box_outline_blank"}
      </span>

      {/* Текст кнопки */}
      {title && <TextUI variant="label">{title}</TextUI>}
    </button>
  );
};
