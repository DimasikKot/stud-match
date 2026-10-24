import React from "react";
import logo from "@/shared/images/logo.svg";

import { TextUI } from "@/shared/components/TextUI";
import { ButtonUI } from "@/shared/components/ButtonUI";

export function LoginRegisterCard({
  title,
  subtitle,
  children,
  buttonText,
  onButtonClick,
  isLoading = false,
  descriptionLink,
  backButton,
}: {
  title: string;
  subtitle?: string;
  children?: React.ReactNode;
  buttonText: string;
  onButtonClick: () => void;
  isLoading?: boolean;
  error?: string | null;
  descriptionLink?: {
    text: string;
    onClick: () => void;
  };
  backButton?: {
    text?: string;
    onClick: () => void;
  };
}) {
  const isFirstStep = !backButton;

  return (
    <div className="w-full max-w-200 mx-auto">
      <div className="bg-white rounded-3xl p-8 shadow-xl border border-gray-300">
        <div className="flex justify-start mb-6">
          <img src={logo} alt="Logo" className="w-12 h-12" />
        </div>

        <div className="flex gap-12">
          <div className="flex-1">
            <TextUI variant="title" className="text-left mb-2">
              {title}
            </TextUI>

            {subtitle && (
              <TextUI variant="desc" className="text-left">
                {subtitle}
              </TextUI>
            )}
          </div>

          <div className="flex-1">
            <div>{children}</div>

            {descriptionLink && (
              <div className="flex justify-start mt-4">
                <ButtonUI onClick={descriptionLink.onClick} variant="link">
                  <TextUI variant="link" className="text-blue-600">
                    {descriptionLink.text}
                  </TextUI>
                </ButtonUI>
              </div>
            )}
          </div>
        </div>

        <div className="mt-8 flex items-center justify-between">
          {backButton && (
            <ButtonUI
              onClick={backButton.onClick}
              variant="secondary"
              className="px-6 py-3"
            >
              {backButton.text || "Назад"}
            </ButtonUI>
          )}

          <div className={isFirstStep ? "ml-auto" : ""}>
            <ButtonUI
              onClick={onButtonClick}
              disabled={isLoading}
              className="px-8 py-3"
            >
              {isLoading ? "Загрузка..." : buttonText}
            </ButtonUI>
          </div>
        </div>
      </div>
    </div>
  );
}
