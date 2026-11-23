import { ButtonUI } from "@/shared/components/ButtonUI";
import { useNavigate } from "react-router-dom";

export function NotFound() {
  const navigate = useNavigate();

  return (
    <div className="max-w-6xl mx-auto p-6 items-center flex flex-col bg-white">
      <ButtonUI onClick={() => navigate("/projects")}>
        К списку проектов
      </ButtonUI>
    </div>
  );
}
