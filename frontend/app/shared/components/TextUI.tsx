export const TextUI = ({
  variant = "normal",
  className = "",
  maxLines = 3,
  isSelectable = false,
  isSpan = false,
  children,
}: {
  variant?:
    | "desc"
    | "link"
    | "label"
    | "error"
    | "normal"
    | "subtitle"
    | "title"
    | "logo"
    | "header";
  className?: string;
  maxLines?: number;
  isSelectable?: boolean;
  isSpan?: boolean;
  children: React.ReactNode;
}) =>
  isSpan ? (
    <span
      className={`leading-relaxed
        ${isSelectable ? "select-text" : "select-none"}
        ${
          {
            desc: "text-gray-600 text-sm font-normal",
            link: "text-blue-600 hover:text-blue-800 text-sm font-medium",
            label: "text-gray-700 text-sm font-medium",
            error: "text-red-600 text-sm font-medium",
            normal: "text-base font-medium",
            subtitle: "text-lg font-medium",
            title: "text-xl font-bold",
            logo: "text-2xl font-bold",
            header: "text-3xl font-bold",
          }[variant]
        }
        ${className} ${maxLines && `line-clamp-${maxLines}`}`}
    >
      {children}
    </span>
  ) : (
    <p
      className={`leading-relaxed
        ${isSelectable ? "select-text" : "select-none"}
        ${
          {
            desc: "text-gray-600 text-sm font-normal",
            link: "text-blue-600 hover:text-blue-800 text-sm font-normal",
            label: "text-gray-700 text-sm font-medium",
            error: "text-red-600 text-sm font-medium",
            normal: "text-base font-medium",
            subtitle: "text-base font-bold",
            title: "text-xl font-bold",
            logo: "text-2xl font-bold",
            header: "text-3xl font-bold",
          }[variant]
        }
        ${className} ${maxLines && `line-clamp-${maxLines}`}`}
    >
      {children}
    </p>
  );
