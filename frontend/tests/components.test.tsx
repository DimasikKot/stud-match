// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import toast from "react-hot-toast";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ButtonUI } from "@/shared/components/ButtonUI";
import { CheckboxUI } from "@/shared/components/CheckboxUI";
import { PrivateRoute } from "@/shared/components/PrivateRoute";
import { StatusIndicator } from "@/shared/components/StatusIndicator";
import { TagSelector } from "@/shared/components/TagSelector";
import { TextField } from "@/shared/components/TextField";

vi.mock("react-hot-toast", () => ({
  default: { error: vi.fn(), success: vi.fn() },
}));

afterEach(() => {
  cleanup();
  localStorage.clear();
  vi.clearAllMocks();
});

describe("ButtonUI", () => {
  it("вызывает onClick и не пускает клик к родителю", () => {
    const onClick = vi.fn();
    const onParentClick = vi.fn();
    render(
      <div onClick={onParentClick}>
        <ButtonUI onClick={onClick}>Сохранить</ButtonUI>
      </div>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Сохранить" }));

    expect(onClick).toHaveBeenCalledOnce();
    expect(onParentClick).not.toHaveBeenCalled();
  });

  it("без onClick показывает подсказку", () => {
    render(<ButtonUI>Кнопка</ButtonUI>);
    fireEvent.click(screen.getByRole("button"));
    expect(toast.success).toHaveBeenCalledWith("Кнопка без действия");
  });

  it("disabled-кнопка не реагирует на клик", () => {
    const onClick = vi.fn();
    render(
      <ButtonUI onClick={onClick} disabled>
        Нет
      </ButtonUI>,
    );
    const button = screen.getByRole("button");
    fireEvent.click(button);
    expect(button).toHaveProperty("disabled", true);
    expect(onClick).not.toHaveBeenCalled();
  });

  it("hidden не рендерит кнопку", () => {
    render(<ButtonUI hidden>Скрыта</ButtonUI>);
    expect(screen.queryByRole("button")).toBeNull();
  });
});

describe("CheckboxUI", () => {
  it.each([
    [true, "check_box"],
    [false, "check_box_outline_blank"],
  ])("value=%s показывает иконку %s", (value, icon) => {
    const onClick = vi.fn();
    render(<CheckboxUI value={value} onClick={onClick} title="Запомнить" />);

    const button = screen.getByRole("button", {
      name: new RegExp("Запомнить"),
    });
    expect(button.textContent).toContain(icon);
    fireEvent.click(button);
    expect(onClick).toHaveBeenCalledOnce();
  });
});

describe("StatusIndicator", () => {
  it.each([
    [true, "bg-green-500"],
    [false, "bg-red-500"],
    [undefined, "bg-gray-500"],
  ])("status=%s → %s", (status, color) => {
    const { container } = render(
      <StatusIndicator status={status as boolean} />,
    );
    expect(container.firstElementChild?.className).toContain(color);
  });
});

describe("TextField", () => {
  const Controlled = (props: {
    onEnter?: () => void;
    onEscape?: () => void;
    isArea?: boolean;
  }) => {
    const [value, setValue] = useState("");
    return (
      <>
        <TextField
          value={value}
          setValue={setValue}
          placeholder="Имя"
          {...props}
        />
        <output>{value}</output>
      </>
    );
  };

  it.each([false, true])("isArea=%s обновляет значение", (isArea) => {
    render(<Controlled isArea={isArea} />);
    const field = screen.getByPlaceholderText("Имя");
    expect(field.tagName).toBe(isArea ? "TEXTAREA" : "INPUT");

    fireEvent.change(field, { target: { value: "Иван" } });

    expect(screen.getByRole("status").textContent).toBe("Иван");
  });

  it("вызывает onEnter и onEscape", () => {
    const onEnter = vi.fn();
    const onEscape = vi.fn();
    render(<Controlled onEnter={onEnter} onEscape={onEscape} />);
    const field = screen.getByPlaceholderText("Имя");

    fireEvent.keyDown(field, { key: "Enter" });
    fireEvent.keyDown(field, { key: "Escape" });
    fireEvent.keyDown(field, { key: "a" });

    expect(onEnter).toHaveBeenCalledOnce();
    expect(onEscape).toHaveBeenCalledOnce();
  });
});

describe("TagSelector", () => {
  it("выбирает B- и I- теги и закрывается", () => {
    const onSelect = vi.fn();
    const onClose = vi.fn();
    render(
      <TagSelector
        currentTag="B-PER"
        tags={{ "B-PER": "Персона" }}
        colors={{ "B-PER": "bg-red-100", "I-PER": "bg-red-50" }}
        onSelect={onSelect}
        onClose={onClose}
      />,
    );

    fireEvent.click(screen.getByText("Не сущность"));
    fireEvent.click(screen.getByText("Персона"));
    fireEvent.click(screen.getByText("I-PER"));

    expect(onSelect.mock.calls).toEqual([["O"], ["B-PER"], ["I-PER"]]);
    expect(onClose).toHaveBeenCalledTimes(3);
    expect(screen.getByText("B-PER").className).toContain("ring-2");
    expect(screen.getByText("I-PER").className).not.toContain("ring-2");
  });
});

describe("PrivateRoute", () => {
  const renderAt = () =>
    render(
      <MemoryRouter initialEntries={["/secret"]}>
        <Routes>
          <Route element={<PrivateRoute />}>
            <Route path="/secret" element={<p>Секрет</p>} />
          </Route>
          <Route path="/login" element={<p>Вход</p>} />
        </Routes>
      </MemoryRouter>,
    );

  it("без токена редиректит на /login", () => {
    renderAt();
    expect(screen.getByText("Вход")).toBeTruthy();
  });

  it("с токеном показывает страницу", () => {
    localStorage.setItem("access_token", "x");
    renderAt();
    expect(screen.getByText("Секрет")).toBeTruthy();
  });
});
