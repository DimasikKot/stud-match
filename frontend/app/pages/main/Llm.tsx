import { useEffect, useRef, useState } from "react";
import toast from "react-hot-toast";

import { Header } from "@/shared/components/Header";
import { ButtonUI } from "@/shared/components/ButtonUI";
import { CheckboxUI } from "@/shared/components/CheckboxUI";
import { TextField } from "@/shared/components/TextField";
import { TextUI } from "@/shared/components/TextUI";
import { fetchFiles, type FileListResponse } from "@/shared/api/file";
import {
  createLLMTask,
  fetchLLMTask,
  splitThinking,
  type LLMTaskStatus,
} from "@/shared/api/llm";

const STATUS_TEXT: Record<LLMTaskStatus, string> = {
  queued: "В очереди…",
  running: "Генерация…",
  done: "Готово",
  error: "Ошибка",
};

export function Llm() {
  const abortRef = useRef<AbortController | null>(null);

  const [files, setFiles] = useState<FileListResponse[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [prompt, setPrompt] = useState("");
  const [enableThinking, setEnableThinking] = useState(true);
  const [output, setOutput] = useState("");
  const [status, setStatus] = useState<LLMTaskStatus | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    fetchFiles()
      .then((response) => setFiles(response.data))
      .catch(() => {});
    return () => abortRef.current?.abort();
  }, []);

  const toggleFile = (id: number) =>
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id],
    );

  const handleSend = async () => {
    if (!prompt.trim()) {
      toast.error("Введите запрос");
      return;
    }
    const controller = new AbortController();
    abortRef.current = controller;
    setOutput("");
    setStatus(null);
    setIsGenerating(true);
    try {
      const task = await createLLMTask({
        prompt,
        file_ids: selectedIds,
        enable_thinking: enableThinking,
      });
      setStatus(task.status);

      // Стриминга нет — опрашиваем статус до завершения задачи
      while (!controller.signal.aborted) {
        await new Promise((resolve) => setTimeout(resolve, 2000));
        if (controller.signal.aborted) break;
        const current = await fetchLLMTask(task.task_id);
        setStatus(current.status);
        if (current.status === "done") {
          setOutput(current.result);
          break;
        }
        if (current.status === "error") {
          toast.error(current.error || "Ошибка генерации");
          break;
        }
      }
    } catch {
      // ошибка уже показана тостом либо генерацию остановили
    } finally {
      setIsGenerating(false);
      abortRef.current = null;
    }
  };

  const { thinking, answer } = splitThinking(output);

  return (
    <div className="min-h-screen flex flex-col">
      <Header title="Нейросеть" />

      <div className="max-w-6xl mx-auto m-6 mb-20 w-full flex flex-col gap-6">
        {/* Запрос */}
        <div className="bg-white border border-gray-300 rounded-3xl p-6 flex flex-col gap-4">
          <TextUI variant="title">Запрос к нейросети</TextUI>

          <TextField
            value={prompt}
            setValue={setPrompt}
            isArea
            rows={5}
            placeholder="Например: кратко перескажи содержимое файлов"
            disabled={isGenerating}
          />

          <div className="flex items-center justify-between gap-4 flex-wrap">
            <CheckboxUI
              value={enableThinking}
              onClick={() => setEnableThinking((prev) => !prev)}
              title="Режим рассуждений (thinking)"
            />
            {isGenerating ? (
              <ButtonUI
                variant="secondary"
                onClick={() => abortRef.current?.abort()}
              >
                Не ждать ответ
              </ButtonUI>
            ) : (
              <ButtonUI onClick={handleSend}>Отправить</ButtonUI>
            )}
          </div>
        </div>

        {/* Файлы из БД */}
        <div className="bg-white border border-gray-300 rounded-3xl p-6">
          <TextUI variant="title" className="mb-4">
            Файлы для контекста (выбрано: {selectedIds.length})
          </TextUI>
          {files.length === 0 ? (
            <TextUI variant="desc">
              Файлов нет, загрузите их на странице «Файлы»
            </TextUI>
          ) : (
            <div className="flex flex-col gap-1">
              {files.map((file) => (
                <CheckboxUI
                  key={file.id}
                  value={selectedIds.includes(file.id)}
                  onClick={() => toggleFile(file.id)}
                  title={`#${file.id} ${file.name}`}
                />
              ))}
            </div>
          )}
        </div>

        {/* Ответ */}
        {(output || status) && (
          <div className="bg-white border border-gray-300 rounded-3xl p-6 flex flex-col gap-4">
            <div className="flex items-center justify-between gap-4">
              <TextUI variant="title">Ответ</TextUI>
              {status && <TextUI variant="desc">{STATUS_TEXT[status]}</TextUI>}
            </div>
            {thinking && (
              <details open={!answer} className="bg-gray-50 rounded-2xl p-4">
                <summary className="cursor-pointer text-gray-500">
                  Рассуждения
                </summary>
                <p className="whitespace-pre-wrap text-gray-500 mt-2">
                  {thinking}
                </p>
              </details>
            )}
            {answer && <p className="whitespace-pre-wrap">{answer}</p>}
          </div>
        )}
      </div>
    </div>
  );
}
