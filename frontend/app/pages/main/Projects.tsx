import { useNavigate } from "react-router-dom";

import { ButtonUI } from "@/shared/components/ButtonUI";

export function Projects() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen">
      <div className="flex p-6 justify-center">
        <div className="max-w-6xl w-full flex flex-col md:flex-row gap-8 items-center justify-center">
          <ButtonUI onClick={() => navigate("/files")}>
            Перейти к файлам
          </ButtonUI>
        </div>
      </div>
    </div>
  );
}
