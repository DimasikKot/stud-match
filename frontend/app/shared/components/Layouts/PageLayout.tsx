import { TextUI } from "../UI/TextUI";

export function PageLayout({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="p-5">
      <TextUI variant="title">{title}</TextUI>
      {children}
    </div>
  );
}
