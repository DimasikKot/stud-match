import { useState } from "react";

import { TextUI } from "@/shared/components/UI/TextUI";

const formatPrimitive = (value: unknown): string => {
  if (value === null) return "null";
  if (value === undefined) return "-";
  if (Array.isArray(value)) return JSON.stringify(value);
  return String(value);
};

const formatMetrics = (metrics?: Record<string, unknown> | null): string => {
  if (!metrics || typeof metrics !== "object") return "";

  const lines: string[] = [];

  const walk = (value: Record<string, unknown>, depth: number) => {
    for (const [key, item] of Object.entries(value)) {
      const pad = "  ".repeat(depth);
      if (item && typeof item === "object" && !Array.isArray(item)) {
        lines.push(`${pad}${key}:`);
        walk(item as Record<string, unknown>, depth + 1);
      } else {
        lines.push(`${pad}${key}: ${formatPrimitive(item)}`);
      }
    }
  };

  walk(metrics, 0);
  return lines.join("\n");
};

export const TooltipUI = ({
  content,
  children,
  className: customClassName,
  isJSON = false,
  placement = "right",
}: {
  content?: string | Record<string, unknown> | null;
  children: React.ReactNode;
  className?: string;
  isJSON?: boolean;
  placement?: "right" | "top" | "bottom";
}) => {
  const [visible, setVisible] = useState(false);

  const placementClass = {
    right: "left-full top-1/4 -translate-y-5/6",
    top: "bottom-full left-1/2 -translate-x-1/2",
    bottom: "top-full left-1/2 -translate-x-1/2",
  }[placement];

  return (
    <div
      className={`relative ${customClassName ?? ""}`}
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
    >
      {children}

      {visible && content && (
        <div
          className={`absolute z-50 max-h-160 w-max rounded-md overflow-y-auto bg-gray-800 px-3 py-2 border border-gray-300 ${placementClass}`}
        >
          <TextUI variant="label" className="text-white whitespace-pre-wrap">
            {isJSON && typeof content !== "string"
              ? formatMetrics(content)
              : String(content)}
          </TextUI>
        </div>
      )}
    </div>
  );
};
