export const TextUI = ({
  variant = "normal",
  className: customClassName,
  maxLines = 3,
  isSelectable = false,
  span = false,
  title,
  children,
}: {
  variant?:
    | "desc"
    | "link"
    | "error"
    | "label"
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
}) => {
  const className = `leading-relaxed
        ${
          {
            desc: "text-gray-600 text-sm font-normal",
            link: "text-blue-600 hover:text-blue-800 text-sm font-medium",
            error: "text-red-600 text-sm font-medium",
            label: "text-sm font-medium",
            normal: "text-base font-medium",
            subtitle: "text-lg font-medium",
            title: "text-2xl font-light",
            header: "text-2xl font-semibold",
          }[variant]
        }
        ${customClassName}
        ${isSelectable ? "select-text" : "select-none"}
        ${maxLines && `line-clamp-${maxLines}`}`;

  return span ? (
    <span title={title} className={className}>
      {children}
    </span>
  ) : (
    <p title={title} className={className}>
      {children}
    </p>
  );
};
