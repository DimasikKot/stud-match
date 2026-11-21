import { useNavigate } from "react-router-dom";

import { InfoCard } from "@/shared/components/InfoCard";
import { InfoCardBig } from "@/shared/components/InfoCardBig";

export function Projects() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen">
      <div className="flex p-6 justify-center">
        <div className="max-w-6xl w-full flex flex-col md:flex-row gap-8 items-center justify-center">
          <InfoCard
            icon="rocket_launch"
            iconClassName="bg-emerald-100 text-emerald-600"
            title="Наши плюсы"
            description="+ + +"
          />

          <InfoCardBig
            icon="auto_awesome"
            title="Распределения"
            description="-"
            buttonText="Перейти к -"
            onClick={() => navigate("/distribution")}
          />

          <InfoCard
            icon="bolt"
            iconClassName="bg-blue-100 text-blue-600"
            title="Мы предлагаем"
            description="-"
          />
        </div>
      </div>
    </div>
  );
}
