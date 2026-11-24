import { TextUI } from "@/shared/components/UI/TextUI";

export const StatusUI = ({
  value,
  title,
  className: customClassName,
}: {
  value?: boolean;
  title?: string;
  className?: string;
}) => {
  const className = `
    flex items-center w-fit gap-2 ${customClassName}
  `;

  return (
    <div className={className}>
      <div
        className={`rounded-full h-3 w-3 ${value === undefined ? "bg-gray-500" : value === true ? "bg-green-500" : "bg-red-500"}`}
      />

      {title && <TextUI variant="label">{title}</TextUI>}
    </div>
  );
};
