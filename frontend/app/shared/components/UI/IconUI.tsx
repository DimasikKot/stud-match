export const IconUI = ({
  size = "20px",
  icon,
  color = "white",
  className = "",
  onClick,
  title,
}: {
  size: string;
  icon: string;
  color?: string;
  className?: string;
  onClick?: () => void;
  title?: string;
}) => {
  return onClick ? (
    <button
      className={`flex items-center justify-center cursor-pointer ${className}`}
      onClick={onClick}
      title={title}
    >
      <span
        className={`material-icons leading-none overflow-clip select-none text-${color}`}
        style={{ fontSize: size, lineHeight: 1, width: size }}
      >
        {icon}
      </span>
    </button>
  ) : (
    <span
      className={`material-icons leading-none overflow-clip select-none text-${color} ${className}`}
      style={{ fontSize: size, lineHeight: 1, width: size }}
      title={title}
    >
      {icon}
    </span>
  );
};
