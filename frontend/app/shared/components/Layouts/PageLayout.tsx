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
    <div className="p-5 mb-80">
      <div className="mx-4">
        <TextUI variant="header">{title}</TextUI>
      </div>

      <div className={className}>{children}</div>
    </div>
  );
}
