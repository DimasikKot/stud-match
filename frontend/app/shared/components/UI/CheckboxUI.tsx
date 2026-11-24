import { IconUI } from "./IconUI";
import { TextUI } from "./TextUI";

export const CheckboxUI = ({
  value,
  onClick,
  title,
  className: customClassName,
}: {
  value: boolean;
  onClick: () => void;
  title?: string;
  className?: string;
}) => {
  const className = `
    flex items-center w-max cursor-pointer gap-2 p-2 ${title && "px-4"}  hover:bg-gray-200 rounded-full transition-colors ${customClassName}
  `;

  return (
    <button type="button" onClick={onClick} className={className}>
      <IconUI
        icon={value ? "check_box" : "check_box_outline_blank"}
        color={value ? "blue-600" : "gray-400"}
      />

      {title && <TextUI variant="label">{title}</TextUI>}
    </button>
  );
};
