import { TextUI } from "./TextUI";

export function TagSelector({
  currentTag,
  tags,
  colors,
  onSelect,
  onClose,
  position,
}: {
  currentTag: string | null;
  tags: Record<string, string>;
  colors: Record<string, string>;
  onSelect: (tag: string) => void;
  onClose: () => void;
  position?: { x: number; y: number };
}) {
  return (
    <div
      className="fixed bg-white shadow-2xl border border-gray-300 rounded-2xl z-50 w-80 max-h-96 overflow-clip"
      style={{
        left: position?.x ?? 0,
        top: position?.y ?? 0,
      }}
      onClick={(e) => e.stopPropagation()}
      onScroll={(e) => e.stopPropagation()}
    >
      <div className="py-2 w-80 h-96 overflow-auto">
        <button
          key="O"
          onClick={() => {
            onSelect("O");
            onClose();
          }}
          className="w-full px-2 py-2.5 text-left hover:bg-gray-100 flex items-center gap-3 transition-colors"
        >
          <span
            className={`font-mono text-md font-medium px-1 py-0.5 h-min w-15 text-center rounded`}
          >
            O
          </span>

          <TextUI variant="normal">Не сущность</TextUI>
        </button>

        {Object.entries(tags).map(([tagKey, label]) => {
          const iTag = tagKey.replace("B-", "I-");

          return (
            <div key={tagKey} className="px-2 py-2.5 gap-2 flex flex-row">
              <button
                onClick={() => {
                  onSelect(tagKey);
                  onClose();
                }}
                className="p-1 w-full text-left hover:bg-gray-100 flex items-center gap-3 transition-colors"
              >
                <span
                  className={`font-mono text-sm font-medium px-1 py-0.5 w-14 h-min text-center rounded ${colors[tagKey]} ${currentTag === tagKey ? "ring-2 ring-gray-800" : ""}`}
                >
                  {tagKey}
                </span>

                <TextUI variant="normal">{label}</TextUI>
              </button>

              <button
                key={iTag}
                onClick={() => {
                  onSelect(iTag);
                  onClose();
                }}
                className="px-1 w-min text-left hover:bg-gray-100 flex items-center gap-3 transition-colors"
              >
                <span
                  className={`font-mono text-sm font-medium px-1 py-0.5 w-13 text-center rounded ${colors[iTag]} ${currentTag === iTag ? "ring-2 ring-gray-800" : ""}`}
                >
                  {iTag}
                </span>
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
