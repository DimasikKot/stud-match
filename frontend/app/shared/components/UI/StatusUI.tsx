import { TextUI } from "@/shared/components/UI/TextUI";

export const StatusUI = ({
  status,
  title,
  className: customClassName,
}: {
  status?: boolean;
  title?: string;
  className?: string;
}) => {
  const className = `
    flex items-center w-fit gap-2 ${customClassName}
  `;

  return (
    <div className={className}>
      <div
        className={`rounded-full h-3 w-3 ${status === undefined ? "bg-gray-500" : status === true ? "bg-green-500" : "bg-red-500"}`}
      />

      {title && <TextUI variant="label">{title}</TextUI>}
    </div>
  );
};
