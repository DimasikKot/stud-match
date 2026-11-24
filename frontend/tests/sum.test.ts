import { test, expect } from "vitest";

// Тестирование суммы

const sum = (a: number, b: number) => {
  return a + b;
};

test("сумма двух чисел", () => {
  expect(sum(1, 2)).toBe(3);
});
