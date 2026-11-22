import { useNavigate } from "react-router-dom";
import { useState } from "react";

import { ButtonPage } from "@/shared/components/ButtonPage";
import { TextUI } from "@/shared/components/TextUI";
import { ButtonUI } from "@/shared/components/ButtonUI";
import { StatusIndicator } from "@/shared/components/StatusIndicator";
import { TextField } from "@/shared/components/TextField";
import { CheckboxUI } from "@/shared/components/CheckboxUI";

export function Components() {
  const navigate = useNavigate();
  const [textValue, setTextValue] = useState("");
  const [checkboxValue, setCheckboxValue] = useState(false);

  return (
    <>
      <div className="max-w-6xl mx-auto m-6 mb-80 bg-white">
        <ButtonPage onClick={() => navigate("/")} />

        <div className="flex flex-col gap-16">
          {/* TextUI */}
          <div>
            <TextUI variant="header" className="mb-6">
              TextUI
            </TextUI>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
              <div className="bg-white p-6 rounded-3xl border border-gray-200">
                <TextUI variant="desc">desc (описание)</TextUI>
              </div>
              <div className="bg-white p-6 rounded-3xl border border-gray-200">
                <TextUI variant="label">label (метка)</TextUI>
              </div>
              <div className="bg-white p-6 rounded-3xl border border-gray-200">
                <TextUI variant="normal">normal (обычный)</TextUI>
              </div>
              <div className="bg-white p-6 rounded-3xl border border-gray-200">
                <TextUI variant="title">title (заголовок)</TextUI>
              </div>
              <div className="bg-white p-6 rounded-3xl border border-gray-200">
                <TextUI variant="header">header (большой заголовок)</TextUI>
              </div>
            </div>
          </div>

          {/* ButtonUI */}
          <div>
            <TextUI variant="header" className="mb-6">
              ButtonUI
            </TextUI>
            <div className="flex flex-wrap gap-4">
              <ButtonUI variant="primary">Primary Button</ButtonUI>
              <ButtonUI variant="secondary">Secondary Button</ButtonUI>
              <ButtonUI variant="link">Link Button</ButtonUI>
              <ButtonUI variant="primary" disabled>
                Primary Button Disabled
              </ButtonUI>
              <ButtonUI variant="secondary" disabled>
                Secondary Button Disabled
              </ButtonUI>
              <ButtonUI variant="link" disabled>
                Link Button Disabled
              </ButtonUI>
            </div>
          </div>

          {/*CheckboxUI */}
          <div>
            <TextUI variant="header" className="mb-6">
              CheckboxUI
            </TextUI>
            <div className="flex items-center gap-4">
              <CheckboxUI
                value={checkboxValue}
                title="Checked"
                onClick={() => setCheckboxValue(!checkboxValue)}
              />
              <CheckboxUI
                value={!checkboxValue}
                title="Unchecked"
                onClick={() => setCheckboxValue(!checkboxValue)}
              />
              <CheckboxUI
                value={checkboxValue}
                onClick={() => setCheckboxValue(!checkboxValue)}
              />
            </div>
          </div>

          {/* StatusIndicator */}
          <div>
            <TextUI variant="header" className="mb-6">
              StatusIndicator
            </TextUI>
            <div className="flex items-center gap-8">
              <div className="flex items-center gap-3">
                <StatusIndicator status={true} />
                <TextUI variant="desc">Online (true)</TextUI>
              </div>
              <div className="flex items-center gap-3">
                <StatusIndicator status={false} />
                <TextUI variant="desc">Offline (false)</TextUI>
              </div>
            </div>
          </div>

          {/* TextField */}
          <div>
            <TextUI variant="header" className="mb-6">
              TextField
            </TextUI>
            <div className="max-w-md space-y-6">
              <div>
                <TextUI variant="label" className="mb-1 block">
                  Обычное поле
                </TextUI>
                <TextField
                  value={textValue}
                  setValue={setTextValue}
                  placeholder="Введите текст..."
                />
              </div>

              <div>
                <TextUI variant="label" className="mb-1 block">
                  Многострочное поле
                </TextUI>
                <TextField
                  value={textValue}
                  setValue={setTextValue}
                  placeholder="Введите длинный текст..."
                  isArea
                  rows={4}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
