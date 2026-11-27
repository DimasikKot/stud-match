import { useMemo, useRef, useState } from "react";

import type { SkillResponse } from "@/shared/api/skills";
import { IconUI } from "@/shared/components/UI/IconUI";
import { InputUI } from "@/shared/components/UI/InputUI";
import { TextUI } from "@/shared/components/UI/TextUI";

const clampLevel = (level: number): number =>
  Math.min(1, Math.max(0, Math.round(level * 100) / 100));

export const SkillsPicker = ({
  skills,
  value,
  onChange,
  placeholder = "Начните вводить название навыка",
}: {
  skills: SkillResponse[];
  value: Record<string, number>;
  onChange: (levels: Record<string, number>) => void;
  placeholder?: string;
}) => {
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const blurTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  const suggestions = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return skills
      .filter((skill) => !(skill.name in value))
      .filter((skill) =>
        normalized ? skill.name.toLowerCase().includes(normalized) : true,
      )
      .slice(0, 8);
  }, [skills, value, query]);

  const addSkill = (name: string) => {
    if (!(name in value)) {
      onChange({ ...value, [name]: 1 });
    }
    setQuery("");
    setIsOpen(false);
  };

  const setLevel = (name: string, raw: string) => {
    const parsed = Number.parseFloat(raw.replace(",", "."));
    if (Number.isNaN(parsed)) return;
    onChange({ ...value, [name]: clampLevel(parsed) });
  };

  const removeSkill = (name: string) => {
    const next = { ...value };
    delete next[name];
    onChange(next);
  };

  return (
    <div
      className="relative"
      onFocus={() => setIsOpen(true)}
      onBlur={() => {
        blurTimeout.current = setTimeout(() => setIsOpen(false), 150);
      }}
    >
      <InputUI
        value={query}
        onChange={(event) => {
          setQuery(event.target.value);
          setIsOpen(true);
        }}
        placeholder={placeholder}
        onEnter={() => {
          if (suggestions.length === 1) {
            addSkill(suggestions[0].name);
          }
        }}
      />

      {isOpen && suggestions.length > 0 && (
        <div className="absolute z-20 mt-1 w-full border border-gray-300 bg-white shadow-lg max-h-48 overflow-y-auto">
          {suggestions.map((skill) => (
            <button
              key={skill.id}
              type="button"
              className="w-full px-3 py-1.5 text-left hover:bg-gray-100"
              onMouseDown={(event) => {
                event.preventDefault();
                if (blurTimeout.current) clearTimeout(blurTimeout.current);
                addSkill(skill.name);
              }}
            >
              <TextUI variant="normal" span>
                {skill.name}
              </TextUI>
            </button>
          ))}
        </div>
      )}

      {Object.keys(value).length > 0 && (
        <div className="mt-2 flex flex-col gap-1">
          {Object.entries(value).map(([name, level]) => (
            <div
              key={name}
              className="flex items-center gap-2 border border-gray-300 px-2 py-1"
            >
              <TextUI variant="label" className="flex-1">
                {name}
              </TextUI>
              <InputUI
                value={String(level)}
                onChange={(event) => setLevel(name, event.target.value)}
                placeholder="0.00 - 1.00"
                className="w-24 px-2 py-0.5 text-sm"
              />
              <IconUI
                name="close"
                size="16px"
                onClick={() => removeSkill(name)}
                className="cursor-pointer text-gray-500 hover:text-gray-800"
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
