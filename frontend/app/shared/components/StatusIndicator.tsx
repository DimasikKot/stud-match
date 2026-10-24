export const StatusIndicator = ({
  status,
  className = "",
}: {
  status: boolean;
  className?: string;
}) => (
  <div
    className={`rounded-full h-3 w-3 ${status === true ? "bg-green-500" : "bg-red-500"} ${className}`}
  />
);
