import MockAdapter from "axios-mock-adapter";
import toast from "react-hot-toast";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import api from "@/shared/api/axios";
import {
  deleteFile,
  fetchFiles,
  fileDownloadUrl,
  fileViewUrl,
  uploadFiles,
} from "@/shared/api/file";
import {
  fetchBackendHealth,
  fetchPostgresHealth,
  fetchRedisHealth,
  fetchRustfsHealth,
} from "@/shared/api/healths";
import {
  createLLMTask,
  fetchLLMTask,
  splitThinking,
  streamLLMTask,
} from "@/shared/api/llm";

vi.mock("react-hot-toast", () => ({
  default: { error: vi.fn(), success: vi.fn() },
}));

let mock: MockAdapter;

beforeEach(() => {
  mock = new MockAdapter(api);
  vi.clearAllMocks();
});

afterEach(() => {
  mock.restore();
  vi.unstubAllGlobals();
});

describe("file api", () => {
  it("строит ссылки на просмотр и скачивание", () => {
    expect(fileViewUrl(5)).toMatch(/\/files\/5\/view$/);
    expect(fileDownloadUrl(5)).toMatch(/\/files\/5\/download$/);
  });

  it("uploadFiles отправляет все файлы в поле files", async () => {
    mock.onPost("/files/").reply((config) => {
      const form = config.data as FormData;
      const names = form.getAll("files").map((f) => (f as File).name);
      return [200, names.map((name, id) => ({ id, name }))];
    });

    const files = [new File(["a"], "a.txt"), new File(["b"], "b.pdf")];
    const result = await uploadFiles(files);

    expect(result.map((f) => f.name)).toEqual(["a.txt", "b.pdf"]);
  });

  it("fetchFiles передаёт project_id только если он задан", async () => {
    mock.onGet("/files/").reply((config) => [200, { data: [config.params] }]);

    expect((await fetchFiles()).data[0]).toEqual({});
    expect((await fetchFiles(3)).data[0]).toEqual({ project_id: 3 });
  });

  it("deleteFile возвращает ответ сервера", async () => {
    mock.onDelete("/files/7").reply(200, { success: true, detail: "ok" });
    expect(await deleteFile(7)).toEqual({ success: true, detail: "ok" });
  });

  it("ошибки показываются тостом и пробрасываются", async () => {
    mock.onDelete("/files/7").reply(404, { detail: "Файл не найден" });

    await expect(deleteFile(7)).rejects.toBeTruthy();
    expect(toast.error).toHaveBeenCalledWith("Файл не найден");
  });
});

describe("healths api", () => {
  const cases = [
    ["backend", fetchBackendHealth],
    ["postgres", fetchPostgresHealth],
    ["redis", fetchRedisHealth],
    ["rustfs", fetchRustfsHealth],
  ] as const;

  it.each(cases)("%s: возвращает метрики", async (name, fetchHealth) => {
    const body = { success: true, detail: name, metrics: { a: 1 } };
    mock.onGet(`/healths/${name}`).reply(200, body);
    expect(await fetchHealth()).toEqual(body);
  });

  it.each(cases)(
    "%s: при ошибке возвращает undefined",
    async (name, fetchHealth) => {
      mock.onGet(`/healths/${name}`).reply(500, { detail: "down" });
      expect(await fetchHealth()).toBeUndefined();
      expect(toast.error).toHaveBeenCalledWith("down");
    },
  );
});

describe("llm api", () => {
  it("createLLMTask и fetchLLMTask", async () => {
    const task = { task_id: "t1", status: "queued", result: "", error: "" };
    mock.onPost("/llms/tasks").reply((config) => {
      expect(JSON.parse(config.data)).toEqual({ prompt: "hi", file_ids: [1] });
      return [200, task];
    });
    mock.onGet("/llms/tasks/t1").reply(200, { ...task, status: "done" });

    expect(await createLLMTask({ prompt: "hi", file_ids: [1] })).toEqual(task);
    expect((await fetchLLMTask("t1")).status).toBe("done");
  });

  it("createLLMTask пробрасывает ошибку валидации", async () => {
    mock
      .onPost("/llms/tasks")
      .reply(422, { detail: [{ loc: ["body", "prompt"], msg: "required" }] });

    await expect(
      createLLMTask({ prompt: "", file_ids: [] }),
    ).rejects.toBeTruthy();
    expect(toast.error).toHaveBeenCalled();
  });

  const streamOf = (chunks: string[]) =>
    new ReadableStream<Uint8Array>({
      start(controller) {
        const encoder = new TextEncoder();
        chunks.forEach((c) => controller.enqueue(encoder.encode(c)));
        controller.close();
      },
    });

  it("streamLLMTask отдаёт части по мере получения", async () => {
    const fetchMock = vi.fn(async () => new Response(streamOf(["При", "вет"])));
    vi.stubGlobal("fetch", fetchMock);
    const controller = new AbortController();
    const chunks: string[] = [];

    await streamLLMTask("t1", (c) => chunks.push(c), controller.signal);

    expect(chunks.join("")).toBe("Привет");
    const [url, init] = fetchMock.mock.calls[0] as unknown as [
      string,
      RequestInit,
    ];
    expect(url).toMatch(/\/llms\/tasks\/t1\/stream$/);
    expect(init).toEqual({ credentials: "include", signal: controller.signal });
  });

  it("streamLLMTask корректно склеивает разрезанный UTF-8 символ", async () => {
    const bytes = new TextEncoder().encode("ё");
    const body = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(bytes.slice(0, 1));
        controller.enqueue(bytes.slice(1));
        controller.close();
      },
    });
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(body)),
    );
    const chunks: string[] = [];

    await streamLLMTask("t1", (c) => chunks.push(c));

    expect(chunks.join("")).toBe("ё");
  });

  it("streamLLMTask бросает ошибку при неуспешном ответе", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("nope", { status: 404 })),
    );

    await expect(streamLLMTask("t1", vi.fn())).rejects.toThrow(
      "Ошибка стрима 404",
    );
    expect(toast.error).toHaveBeenCalledWith("Ошибка стрима 404");
  });

  it("streamLLMTask бросает ошибку, если нет тела ответа", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(null)),
    );
    await expect(streamLLMTask("t1", vi.fn())).rejects.toThrow(
      "Ошибка стрима 200",
    );
  });

  it.each([
    ["без рассуждений", "ответ", { thinking: "", answer: "ответ" }],
    [
      "полный ответ",
      "<think>\n думаю \n</think>\n\nответ ",
      { thinking: "думаю", answer: "ответ" },
    ],
    [
      "рассуждение ещё идёт",
      "<think>думаю дальше",
      { thinking: "думаю дальше", answer: "" },
    ],
  ])("splitThinking: %s", (_, text, expected) => {
    expect(splitThinking(text)).toEqual(expected);
  });
});
