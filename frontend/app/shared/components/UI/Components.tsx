import { Children, useState } from "react";

import { TextUI } from "@/shared/components/UI/TextUI";
import { ButtonUI } from "@/shared/components/UI/ButtonUI";
import { StatusUI } from "@/shared/components/UI/StatusUI";
import { InputUI } from "@/shared/components/UI/InputUI";
import { CheckboxUI } from "@/shared/components/UI/CheckboxUI";
import { PageLayout } from "@/shared/components/Layouts/PageLayout";
import { IconUI } from "@/shared/components/UI/IconUI";
import userIcon from "@/shared/images/circle-user-regular-full.svg";
import { IconSvgUI } from "@/shared/components/UI/IconSvgUI";
import toast from "react-hot-toast";

const ComponentsDiv = ({
  title,
  children,
}: {
  title?: string;
  children: React.ReactNode;
}) => {
  return (
    <div>
      {title && <TextUI variant="header">{title}</TextUI>}

      <div className="grid grid-cols-3 gap-4 bg-gray-300">
        <div className="flex flex-col bg-gray-100 gap-2">
          <TextUI variant="title">Без обертки</TextUI>
          {Children.map(children, (child) => (
            <div className="bg-amber-100/70">{child}</div>
          ))}
        </div>

        {/* <div className="flex flex-col bg-gray-100 gap-2">
          <TextUI variant="title">Ширина w-full (100%)</TextUI>
          {Children.map(children, (child) => (
            <div className="bg-amber-100/70 w-full">{child}</div>
          ))}
        </div> */}

        <div className="flex flex-col bg-gray-100 gap-2">
          <TextUI variant="title">Ширина w-fit (auto)</TextUI>
          {Children.map(children, (child) => (
            <div className="bg-amber-100/70 w-fit">{child}</div>
          ))}
        </div>

        <div className="flex flex-col bg-gray-100 gap-2">
          <TextUI variant="title">Ширина w-full + flex justify-center</TextUI>
          {Children.map(children, (child) => (
            <div className="bg-amber-100/70 flex justify-center w-full">
              {child}
            </div>
          ))}
        </div>
      </div>
    </div>
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
        <IconUI icon="logout" color="text-black" />
        <IconUI icon="logout" size="32px" color="text-[#e91010]" />
        <IconUI icon="logout" size="40px" color="text-gray-600" />
      </ComponentsDiv>

      <ComponentsDiv title="Иконки как кнопки">
        <IconUI
          icon="logout"
          onClick={() => toast.success("Кнопка не настроена")}
        />
        <IconUI
          icon="logout"
          size="32px"
          color="text-[#e91010]"
          onClick={() => toast.success("Кнопка не настроена")}
        />
        <IconUI
          icon="logout"
          size="40px"
          color="text-gray-600"
          onClick={() => toast.success("Кнопка не настроена")}
        />
      </ComponentsDiv>

      <ComponentsDiv title="Иконки Svg">
        <IconSvgUI src={userIcon} className="w-8 h-8 text-black" />
        <IconSvgUI src={userIcon} className="w-12 h-12 text-[#E91010]" />
        <IconSvgUI src={userIcon} className="w-16 h-16 text-gray-600" />
      </ComponentsDiv>

      <ComponentsDiv title="Кнопки активные">
        <ButtonUI variant="primary">Primary Button</ButtonUI>
        <ButtonUI variant="secondary">Secondary Button</ButtonUI>
        <ButtonUI variant="link">Link Button</ButtonUI>
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
      </ComponentsDiv>

      <ComponentsDiv title="Кнопки с иконками">
        <ButtonUI variant="icon">
          <IconUI icon="logout" />
        </ButtonUI>
        <ButtonUI variant="icon">
          <IconUI icon="logout" size="32px" color="text-[#e91010]" />
        </ButtonUI>
        <ButtonUI variant="icon">
          <IconUI icon="logout" size="40px" />
        </ButtonUI>
      </ComponentsDiv>

      <ComponentsDiv title="Кнопки неактивные с иконками">
        <ButtonUI variant="icon" disabled>
          <IconUI icon="logout" />
        </ButtonUI>
        <ButtonUI variant="icon" disabled>
          <IconUI icon="logout" size="32px" color="text-[#e91010]" />
        </ButtonUI>
        <ButtonUI variant="icon" disabled>
          <IconUI icon="logout" size="40px" />
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
