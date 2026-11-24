export const IconUI = ({
  icon,
  size = "20px",
  color = "black",
  className: iconClassName = "",
  onClick,
  title,
}: {
  icon: string;
  size?: string;
  color?: string;
  className?: string;
  onClick?: () => void;
  title?: string;
}) => {
  const className = `material-icons leading- overflow-clip select-none text-${color}`;

  return onClick ? (
    <button
      className={`flex items-center justify-center cursor-pointer ${iconClassName}`}
      onClick={onClick}
      title={title}
    >
      <span
        className={className}
        style={{ fontSize: size, lineHeight: 1, width: size }}
      >
        {icon}
      </span>
    </button>
  ) : (
    <span
      className={`${className} ${iconClassName}`}
      style={{ fontSize: size, lineHeight: 1, width: size }}
      title={title}
    >
      {icon}
    </span>
  );
};
