import toast from "react-hot-toast";
import { ButtonUI } from "./ButtonUI";

export const PageNavigate = ({
  className,
  currentPage,
  totalPages,
  onBack = () => {
    toast.success("Кнопка назад не настроена");
  },
  onNext = () => {
    toast.success("Кнопка вперёд не настроена");
  },
}: {
  className?: string;
  currentPage: number;
  totalPages: number;
  onBack?: () => void;
  onNext?: () => void;
}) => (
  <div>
    {totalPages > 1 && (
      <div className={`flex justify-center gap-3 ${className}`}>
        <ButtonUI
          onClick={onBack}
          hidden={currentPage <= 1}
          variant="secondary"
        >
          ← Предыдущая
        </ButtonUI>

        <ButtonUI
          onClick={onNext}
          hidden={currentPage >= totalPages}
          variant="secondary"
        >
          Следующая →
        </ButtonUI>
      </div>
    )}
  </div>
);
