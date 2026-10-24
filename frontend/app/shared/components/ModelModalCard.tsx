import { useEffect } from "react";
import type { ModelFullResponse } from "../api/model";
import { ButtonUI } from "./ButtonUI";
import { TextUI } from "./TextUI";

// depricated
export const ModelModalCard = ({
  model,
  onClose,
}: {
  model: ModelFullResponse;
  onClose: () => void;
}) => {
  useEffect(() => {
    // добавляем фейковый шаг в историю
    window.history.pushState({ modal: true }, "");

    window.addEventListener("popstate", onClose);
  }, [onClose]);

  return (
    <div
      className="
        fixed inset-0 z-50
        bg-black/50 backdrop-blur-[1px]
        flex items-center justify-center
      "
      // onClick={onClose}
    >
      <div
        className="
          bg-white rounded-2xl pt-6 gap-4
          max-w-6xl max-h-[90vh]
          overflow-clip
          shadow-xl
        "
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex justify-between items-center mb-4 px-6">
          <TextUI variant="title">{model.name}</TextUI>

          <ButtonUI
            onClick={onClose}
            variant="secondary"
            className="material-icons text-gray-600 hover:text-black"
          >
            close
          </ButtonUI>
        </div>

        <div className="h-full max-h-[80vh] overflow-auto">
          {/* Графики */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-4 px-6 pb-6">
            {/* Параметры */}
            {Object.entries(model.parameters).length > 0 && (
              <div className="p-6 border border-orange-200 bg-orange-50/20 rounded-2xl">
                <TextUI
                  variant="header"
                  className="mb-4 text-orange-400"
                  isSelectable
                >
                  Параметры обучения
                </TextUI>

                <div className="space-y-2">
                  {Object.entries(model.parameters).map(([k, v]) => (
                    <div
                      key={k}
                      className="flex justify-between py-1 border-b border-orange-200"
                    >
                      <TextUI
                        className="text-orange-400 w-[45%] overflow-hidden"
                        isSelectable
                      >
                        {k}
                      </TextUI>

                      <TextUI
                        className="text-orange-400 w-[50%] overflow-hidden"
                        isSpan
                        isSelectable
                      >
                        {String(v)}
                      </TextUI>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Метрики */}
            {Object.entries(model.metrics).length > 0 && (
              <div className="p-6 border border-emerald-300 bg-emerald-50/20 rounded-2xl">
                <TextUI
                  variant="header"
                  className="mb-4 text-emerald-500"
                  isSelectable
                >
                  Результаты обучения
                </TextUI>

                <div className="space-y-2">
                  {Object.entries(model.metrics).map(([k, v]) => (
                    <div
                      key={k}
                      className="flex justify-between py-1 border-b border-emerald-300"
                    >
                      <TextUI
                        className="text-emerald-500 w-[45%] overflow-hidden"
                        isSelectable
                      >
                        {k}
                      </TextUI>

                      <TextUI
                        className="text-emerald-500 w-[50%] overflow-hidden"
                        isSpan
                        isSelectable
                      >
                        {String(v)}
                      </TextUI>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Графики */}
            {Object.entries(model.graphs).map(([key, value]) => (
              <div key={key} className="border rounded-2xl p-3">
                <TextUI className="mb-2" isSelectable>
                  {key}
                </TextUI>
                <img
                  src={value}
                  alt={key}
                  className="w-full select-none rounded-lg"
                />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
