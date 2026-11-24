import { TextUI } from "../UI/TextUI";

export function PageLayout({
  title,
  children,
  className = "",
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className="p-5 pb-80 h-screen overflow-y-auto overflow-x-auto">
      <TextUI variant="header" className="mx-4 mb-1">
        {title}
      </TextUI>

      <div className={`${className}`}>{children}</div>
    </div>
  );
}
