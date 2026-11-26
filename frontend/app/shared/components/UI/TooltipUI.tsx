import { useState } from "react";

import { TextUI } from "@/shared/components/UI/TextUI";

const formatPrimitive = (value: unknown): string => {
  if (value === null) return "null";
  if (value === undefined) return "-";
  if (Array.isArray(value)) return JSON.stringify(value);
  return String(value);
};

const isPrimitiveList = (value: unknown[]): boolean =>
  value.every((item) => item === null || typeof item !== "object");

const formatMetrics = (
  spaces: number,
  metrics?: Record<string, unknown> | null,
): string => {
  if (!metrics || typeof metrics !== "object") return "";

  const lines: string[] = [];

  const walk = (value: unknown, depth: number) => {
    const pad = "  ".repeat(depth);

    if (Array.isArray(value)) {
      value.forEach((item, index) => {
        if (item && typeof item === "object") {
          lines.push(`${pad}[${index}]:`);
          walk(item, depth + spaces - 1);
        } else {
          lines.push(`${pad}[${index}]: ${formatPrimitive(item)}`);
        }
      });
      return;
    }

    for (const [key, item] of Object.entries(
      value as Record<string, unknown>,
    )) {
      const isComplexObject =
        item &&
        typeof item === "object" &&
        !(Array.isArray(item) && isPrimitiveList(item));
      if (isComplexObject) {
        lines.push(`${pad}${key}:`);
        walk(item, depth + spaces - 1);
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
  JSONSpaces = 2,
  placement = "right",
}: {
  content?: string | Record<string, unknown>;
  children: React.ReactNode;
  className?: string;
  isJSON?: boolean;
  JSONSpaces?: number;
  placement?: "right" | "top" | "bottom";
}) => {
  const [visible, setVisible] = useState(false);

  const placementClass = {
    right: "left-full top-[100%] -translate-y-[100%]",
    top: "bottom-full left-0 -translate-x-0",
    bottom: "top-full left-0 -translate-x-0",
  }[placement];

  return (
    <div
      className={`relative ${customClassName ?? ""}`}
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
    >
      {children}

      {visible && content && (
        <div>
          <div
            className={`absolute z-50 max-h-140 max-w-200 w-max rounded-md overflow-y-auto bg-gray-900/80 px-3 py-2 border border-gray-300 ${placementClass}`}
          >
            <TextUI variant="label" className="text-white whitespace-pre-wrap">
              {isJSON && typeof content !== "string"
                ? formatMetrics(JSONSpaces, content)
                : String(content)}
            </TextUI>
          </div>
        </div>
      )}
    </div>
  );
};
