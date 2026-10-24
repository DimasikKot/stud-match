import toast from "react-hot-toast";

export const ButtonUI = ({
  onClick = () => {
    toast.success("Кнопка без действия");
  },
  variant = "primary",
  className = "",
  disabled = false,
  hidden = false,
  children,
}: {
  onClick?: React.MouseEventHandler<HTMLButtonElement>;
  variant?: "primary" | "secondary" | "link" | "icon";
  className?: string;
  disabled?: boolean;
  hidden?: boolean;
  children: React.ReactNode;
}) =>
  !hidden && (
    <button
      onClick={(event) => {
        event.stopPropagation(); // Останавливаем всплытие
        onClick?.(event);
        event.preventDefault(); // Отменяем дефолтное поведение
      }}
      disabled={disabled}
      className={`h-min w-max duration-200 select-none transition-colors items-center justify-center
        rounded-full flex
      ${
        {
          primary: `${!disabled ? "bg-blue-600 hover:bg-blue-700" : "bg-gray-600 hover:bg-gray-600"} px-4 py-2 text-white rounded-full shadow-lg font-medium`,
          secondary: `${!disabled ? "text-blue-600 hover:bg-gray-200" : "text-gray-600 hover:text-gray-600"} px-4 py-2 font-medium`,
          icon: `${!disabled ? "text-blue-600 hover:bg-gray-200" : "text-gray-600 hover:text-gray-600"} p-2 -m-2 font-medium`,
          link: `${!disabled ? "text-blue-600 hover:text-blue-800" : "text-gray-600 hover:text-gray-600"} p-1 -m-1 font-normal`,
        }[variant]
      } ${!disabled ? "cursor-pointer" : ""} ${className}`}
    >
      {children}
    </button>
  );
