import { useNavigate } from "react-router-dom";

import { Header } from "@/shared/components/Header";
import { InfoCard } from "@/shared/components/InfoCard";
import { InfoCardBig } from "@/shared/components/InfoCardBig";
import { TextUI } from "@/shared/components/TextUI";

export function Home() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col">
      <Header title="Главная" />

      {/* Центральная область */}
      <div className="flex-1 flex m-6 justify-center">
        <div className="max-w-6xl w-full flex flex-col md:flex-row gap-8 items-center justify-center">
          {/* Левая карточка */}
          <InfoCard
            icon="rocket_launch"
            iconClassName="bg-emerald-100 text-emerald-600"
            title="Наши плюсы"
            description="Современные инструменты разметки, высокая точность и удобный интерфейс для каждого пользователя."
          />

          {/* Центральная */}
          <InfoCardBig
            icon="auto_awesome"
            title="Создать новый проект"
            description="Начните работать с данными уже сегодня!"
            buttonText="Перейти к проектам"
            onClick={() => navigate("/projects")}
          />

          {/* Правая карточка */}
          <InfoCard
            icon="bolt"
            iconClassName="bg-blue-100 text-blue-600"
            title="Мы предлагаем"
            description="Удобную платформу для разметки и работы с данными."
          />
        </div>
      </div>

      {/* Футер */}
      <div className="text-center py-6">
        <TextUI variant="desc">Лаборатория разметки © 2026</TextUI>
      </div>
    </div>
  );
}
