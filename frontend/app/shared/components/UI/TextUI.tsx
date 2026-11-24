export const TextUI = ({
  variant = "normal",
  className = "",
  maxLines = 3,
  isSelectable = false,
  span = false,
  title,
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
    | "header";
  className?: string;
  maxLines?: number;
  isSelectable?: boolean;
  span?: boolean;
  title?: string;
  children: React.ReactNode;
}) =>
  span ? (
    <span
      title={title}
      className={`leading-relaxed
        ${isSelectable ? "select-text" : "select-none"}
        ${
          {
            desc: "text-gray-600 text-sm font-normal",
            link: "text-blue-600 hover:text-blue-800 text-sm font-medium",
            label: "text-sm font-medium",
            error: "text-red-600 text-sm font-medium",
            normal: "text-base font-medium",
            subtitle: "text-lg font-medium",
            title: "text-2xl font-light",
            header: "text-3xl font-bold",
          }[variant]
        }
        ${className} ${maxLines && `line-clamp-${maxLines}`}`}
    >
      {children}
    </span>
  ) : (
    <p
      title={title}
      className={`leading-relaxed
        ${isSelectable ? "select-text" : "select-none"}
        ${
          {
            desc: "text-gray-600 text-sm font-normal",
            link: "text-blue-600 hover:text-blue-800 text-sm font-normal",
            label: "text-sm font-medium",
            error: "text-red-600 text-sm font-medium",
            normal: "text-base font-medium",
            subtitle: "text-base font-bold",
            title: "text-2xl font-light",
            header: "text-3xl font-bold",
          }[variant]
        }
        ${className} ${maxLines && `line-clamp-${maxLines}`}`}
    >
      {children}
    </p>
  );
