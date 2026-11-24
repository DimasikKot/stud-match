import { useState } from "react";

import { TextUI } from "@/shared/components/UI/TextUI";
import { ButtonUI } from "@/shared/components/UI/ButtonUI";
import { StatusUI } from "@/shared/components/UI/StatusUI";
import { InputUI } from "@/shared/components/UI/InputUI";
import { CheckboxUI } from "@/shared/components/UI/CheckboxUI";
import { PageLayout } from "@/shared/components/Layouts/PageLayout";
import { IconUI } from "@/shared/components/UI/IconUI";

export function Components() {
  const [textValue, setTextValue] = useState("");
  const [checkboxValue, setCheckboxValue] = useState(false);

  return (
    <PageLayout title="Компоненты" className="flex flex-col gap-8">
      <TextUI variant="header">Текст</TextUI>

      <div>
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
      </div>

      <TextUI variant="header">Иконки</TextUI>

      <div>
        <IconUI icon="logout" />
        <IconUI icon="logout" size="32px" />
        <IconUI icon="logout" size="40px" />
      </div>

      <TextUI variant="header">Кнопки активные</TextUI>

      <div>
        <ButtonUI variant="primary">Primary Button</ButtonUI>
        <ButtonUI variant="secondary">Secondary Button</ButtonUI>
        <ButtonUI variant="link">Link Button</ButtonUI>
        <ButtonUI variant="icon">
          <IconUI icon="logout" size="24px" />
        </ButtonUI>
      </div>

      <TextUI variant="header">Кнопки неактивные</TextUI>

      <div>
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
      </div>

      <TextUI variant="header">Чекбоксы</TextUI>

      <div>
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
      </div>

      <TextUI variant="header">Статус индикаторы</TextUI>

      <TextUI variant="header">Поля ввода</TextUI>

      <div>
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
      </div>

      <div>
        <StatusUI status={true} />
        <StatusUI status={false} />
        <StatusUI status={undefined} />
        <StatusUI status={true} title="Online" />
        <StatusUI status={false} title="Offline" />
        <StatusUI status={undefined} title="Unknown" />
      </div>
    </PageLayout>
  );
}
