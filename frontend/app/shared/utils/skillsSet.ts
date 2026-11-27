export const skillsSetToNames = (
  skillsSet?: Record<string, unknown> | null,
): string[] => Object.keys(skillsSet ?? {});

export const skillsSetToLevels = (
  skillsSet?: Record<string, unknown> | null,
): Record<string, number> =>
  Object.fromEntries(
    Object.entries(skillsSet ?? {}).map(([name, level]) => [
      name,
      typeof level === "number" ? level : 1,
    ]),
  );
