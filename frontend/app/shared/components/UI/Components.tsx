import { useState } from "react";

import { TextUI } from "@/shared/components/UI/TextUI";
import { ButtonUI } from "@/shared/components/UI/ButtonUI";
import { StatusUI } from "@/shared/components/UI/StatusUI";
import { InputUI } from "@/shared/components/UI/InputUI";
import { CheckboxUI } from "@/shared/components/UI/CheckboxUI";
import { PageLayout } from "@/shared/components/Layouts/PageLayout";
import { IconUI } from "@/shared/components/UI/IconUI";
import userIcon from "@/shared/images/circle-user-regular-full.svg";
import { IconSvgUI } from "@/shared/components/UI/IconSvgUI";

const ComponentsDiv = ({
  title,
  children,
}: {
  title?: string;
  children: React.ReactNode;
}) => {
  return (
    <>
      {title && <TextUI variant="header">{title}</TextUI>}

      <div className="flex flex-col w-fit bg-gray-100">{children}</div>
    </>
  );
};

export function Components() {
  const [textValue, setTextValue] = useState("");
  const [checkboxValue, setCheckboxValue] = useState(false);

  return (
    <PageLayout title="Компоненты" className="flex flex-col gap-8">
      <ComponentsDiv title="Текст">
        <TextUI variant="desc">Пример текста - desc (описание)</TextUI>
        <TextUI variant="link">Пример текста - link (ссылка)</TextUI>
        <TextUI variant="error">Пример текста - error (ошибка)</TextUI>
        <TextUI variant="label">Пример текста - label (метка)</TextUI>
        <TextUI variant="normal">Пример текста - normal (обычный)</TextUI>
        <TextUI variant="subtitle">
          Пример текста - subtitle (подзаголовок)
        </TextUI>
        <TextUI variant="title">Пример текста - title (заголовок)</TextUI>
        <TextUI variant="header">
          Пример текста - header (большой заголовок)
        </TextUI>
      </ComponentsDiv>

      <ComponentsDiv title="Иконки">
        <IconUI icon="logout" color="black" />
        <IconUI icon="logout" size="32px" color="[#e91010]" />
        <IconUI icon="logout" size="40px" color="gray-600" />
      </ComponentsDiv>

      <ComponentsDiv title="Иконки Svg">
        <IconSvgUI src={userIcon} className="w-8 h-8 text-black" />
        <IconSvgUI src={userIcon} className="w-12 h-12 text-[#e91010]" />
        <IconSvgUI src={userIcon} className="w-16 h-16 text-gray-600" />
      </ComponentsDiv>

      <ComponentsDiv title="Кнопки активные">
        <ButtonUI variant="primary">Primary Button</ButtonUI>
        <ButtonUI variant="secondary">Secondary Button</ButtonUI>
        <ButtonUI variant="link">Link Button</ButtonUI>
        <ButtonUI variant="icon">
          <IconUI icon="logout" size="24px" />
        </ButtonUI>
      </ComponentsDiv>

      <ComponentsDiv title="Кнопки неактивные">
        <ButtonUI variant="primary" disabled>
          Primary Button
        </ButtonUI>
        <ButtonUI variant="secondary" disabled>
          Secondary Button
        </ButtonUI>
        <ButtonUI variant="link" disabled>
          Link Button
        </ButtonUI>
        <ButtonUI variant="icon" disabled>
          <IconUI icon="logout" size="24px" />
        </ButtonUI>
      </ComponentsDiv>

      <ComponentsDiv title="Чекбоксы">
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
        <CheckboxUI
          value={!checkboxValue}
          onClick={() => setCheckboxValue(!checkboxValue)}
        />
      </ComponentsDiv>

      <ComponentsDiv title="Поля ввода">
        <InputUI
          value={textValue}
          setValue={setTextValue}
          placeholder="Введите текст..."
        />

        <InputUI
          value={textValue}
          setValue={setTextValue}
          placeholder="Введите длинный текст..."
          isArea
          rows={4}
        />
      </ComponentsDiv>

      <ComponentsDiv title="Статус индикаторы">
        <StatusUI status={true} />
        <StatusUI status={false} />
        <StatusUI status={undefined} />
        <StatusUI status={true} title="Online" />
        <StatusUI status={false} title="Offline" />
        <StatusUI status={undefined} title="Unknown" />
      </ComponentsDiv>
    </PageLayout>
  );
}
