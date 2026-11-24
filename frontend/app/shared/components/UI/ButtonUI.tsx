import toast from "react-hot-toast";

export const ButtonUI = ({
  onClick = () => {
    toast.success("Кнопка без действия");
  },
  variant = "primary",
  className: customClassName,
  title,
  disabled = false,
  hidden = false,
  children,
}: {
  onClick?: React.MouseEventHandler<HTMLButtonElement>;
  variant?: "primary" | "secondary" | "link" | "icon";
  className?: string;
  title?: string;
  disabled?: boolean;
  hidden?: boolean;
  children: React.ReactNode;
}) => {
  const className = `
    h-min duration-200 select-none transition-colors justify-center flex
    ${
      {
        primary: `${!disabled ? "bg-blue-700 hover:bg-blue-800" : "bg-gray-600 hover:bg-gray-600"} px-4 py-2 text-white shadow-lg font-medium w-full`,
        secondary: `${!disabled ? "text-blue-700 hover:bg-gray-200/70" : "text-gray-600 hover:text-gray-600"} px-4 py-2 font-medium w-full`,
        link: `${!disabled ? "text-blue-700 hover:text-blue-800" : "text-gray-600 hover:text-gray-600"} p-1 -m-1 font-normal w-fit`,
        icon: `${!disabled ? "text-blue-700 hover:bg-gray-200/70" : "text-gray-600 hover:text-gray-600"} p-2 -m-2 font-medium w-fit`,
      }[variant]
    } ${!disabled ? "cursor-pointer" : ""} ${customClassName}
  `;

  return (
    !hidden && (
      <button
        onClick={(event) => {
          event.stopPropagation(); // Останавливаем всплытие
          onClick?.(event);
          event.preventDefault(); // Отменяем дефолтное поведение
        }}
        disabled={disabled}
        className={className}
      >
        {title && <span className="sr-only">{title}</span>}

        {children}
      </button>
    )
  );
};
