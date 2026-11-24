export const IconUI = ({
  name,
  size = "24px",
  color,
  className: customClassName,
  onClick,
  title,
}: {
  name: string;
  size?: string;
  color?: string;
  className?: string;
  onClick?: () => void;
  title?: string;
}) => {
  const className = `material-icons select-none ${color}`;

  return onClick ? (
    <button
      className={`flex items-center cursor-pointer ${customClassName}`}
      onClick={onClick}
      title={title}
    >
      <span
        className={className}
        style={{ fontSize: size, lineHeight: 1, width: size }}
      >
        {name}
      </span>
    </button>
  ) : (
    <div className="flex items-center">
      <span
        className={`${className} ${customClassName}`}
        style={{ fontSize: size, lineHeight: 1, width: size, height: size }}
        title={title}
      >
        {name}
      </span>
    </div>
  );
};
