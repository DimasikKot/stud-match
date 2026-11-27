import { FileCard } from "@/shared/components/FileCard";
import {
  rustfsObjectDownloadUrl,
  rustfsObjectViewUrl,
  type RustfsObjectResponse,
  type RustfsObjectStatusValue,
  type RustfsObjectsResponse,
} from "@/shared/api/rustfsObjects";
import { TextUI } from "@/shared/components/UI/TextUI";
import { ButtonUI } from "@/shared/components/UI/ButtonUI";
import { IconUI } from "@/shared/components/UI/IconUI";

const STATUS_LABELS: Record<RustfsObjectStatusValue, string> = {
  not_extracted: "Не извлечено",
  failed: "Ошибки",
  queued: "В очереди",
  extracting: "Извлечение",
  extracted: "Извлечено",
};

export const RustfsObjectsModal = ({
  status,
  response,
  onClose,
}: {
  status: RustfsObjectStatusValue;
  response: RustfsObjectsResponse | undefined;
  onClose: () => void;
}) => {
  const objects: RustfsObjectResponse[] = response?.data ?? [];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white border border-gray-300 w-full max-w-6xl max-h-[85vh]
          flex flex-col overflow-hidden"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-center justify-between gap-4 px-6 py-4 border-b border-gray-300">
          <div className="min-w-0">
            <TextUI variant="title" className="line-clamp-1">
              {STATUS_LABELS[status]}
            </TextUI>
            <TextUI variant="desc" className="mt-1">
              Объектов: {response ? response.count : "..."}
            </TextUI>
          </div>

          <ButtonUI variant="icon" onClick={onClose} title="Закрыть">
            <IconUI size="24px" name="close" />
          </ButtonUI>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4">
          {!response ? (
            <TextUI variant="desc">Загрузка...</TextUI>
          ) : objects.length === 0 ? (
            <TextUI variant="desc">Объектов нет</TextUI>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {objects.map((object) => (
                <div key={object.id} className="flex flex-col gap-1">
                  <FileCard
                    file={{
                      id: object.id,
                      name: `${object.object_key}${object.extension}`,
                      status: object.status,
                      student_fullname: null,
                      feature_set: object.feature_set,
                    }}
                    onClick={() =>
                      window.open(rustfsObjectViewUrl(object.id), "_blank")
                    }
                    onDownloadClick={() =>
                      window.open(rustfsObjectDownloadUrl(object.id), "_blank")
                    }
                  />
                  <TextUI variant="desc">
                    {STATUS_LABELS[object.status]} · {object.model_version}
                  </TextUI>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
