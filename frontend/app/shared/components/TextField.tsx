export const TextField = ({
  value,
  setValue,
  onChange,
  onEnter,
  onEscape,
  autoFocus = false,
  placeholder = "",
  disabled = false,
  name = "input",
  type = "text",
  className = "",
  isArea = false,
  rows = 3,
}: {
  value: string;
  setValue?: React.Dispatch<React.SetStateAction<string>>;
  onChange?: (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement, Element>,
  ) => void;
  onEnter?: () => void;
  onEscape?: () => void;
  autoFocus?: boolean;
  placeholder?: string;
  disabled?: boolean;
  name?: string;
  type?: "text" | "email" | "password";
  className?: string;
  isArea?: boolean;
  rows?: number;
}) => {
  return isArea ? (
    <textarea
      name={name}
      value={value}
      onChange={onChange || ((event) => setValue?.(event.target.value))}
      onKeyDown={(event) => {
        if (event.key === "Enter") {
          onEnter?.();
        }
        if (event.key === "Escape") {
          onEscape?.();
        }
      }}
      autoFocus={autoFocus}
      rows={rows}
      placeholder={placeholder}
      disabled={disabled}
      className={`
        w-full px-3 py-3 rounded-lg
        bg-white
        border border-gray-300
        focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-300
        transition-colors duration-200
        ${className}
      `}
    />
  ) : (
    <input
      name={name}
      value={value}
      onChange={onChange || ((event) => setValue?.(event.target.value))}
      onKeyDown={(event) => {
        if (event.key === "Enter") {
          onEnter?.();
        }
        if (event.key === "Escape") {
          onEscape?.();
        }
      }}
      autoFocus={autoFocus}
      placeholder={placeholder}
      disabled={disabled}
      type={type}
      className={`
      w-full px-3 py-3 rounded-lg
      bg-white
      border border-gray-300
      focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-300
      transition-colors duration-200
      ${className}
    `}
    />
  );
};
