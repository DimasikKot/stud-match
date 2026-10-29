import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import MockAdapter from "axios-mock-adapter";

// Мокаем toast, чтобы errorValidate не рендерил в DOM
vi.mock("react-hot-toast", () => ({
  default: {
    error: vi.fn(),
    success: vi.fn(),
    loading: vi.fn(),
    dismiss: vi.fn(),
  },
}));

import toast from "react-hot-toast";
import api from "@/shared/api/axios";
import {
  registerUser,
  loginUser,
  refreshTokens,
  logoutUser,
  getCurrentUser,
} from "@/shared/api/users";

let mock: MockAdapter;

beforeEach(() => {
  mock = new MockAdapter(api);
  vi.clearAllMocks();
});

afterEach(() => {
  mock.restore();
});

// ============================================================
// USERS API
// ============================================================

describe("registerUser", () => {
  test("успешная регистрация возвращает { id, email }", async () => {
    mock.onPost("/users/register").reply(201, { id: 1, email: "a@a.a" });

    const user = await registerUser({ email: "a@a.a", password: "123456" });

    expect(user).toEqual({ id: 1, email: "a@a.a" });
    expect(toast.error).not.toHaveBeenCalled();
  });

  test("400 с detail строкой → toast + reject", async () => {
    mock
      .onPost("/users/register")
      .reply(400, { detail: "Email already registered" });

    await expect(
      registerUser({ email: "a@a.a", password: "123456" }),
    ).rejects.toBeTruthy();

    expect(toast.error).toHaveBeenCalledWith("Email already registered");
  });

  test("422 с detail-массивом → toast склеивает msg", async () => {
    mock.onPost("/users/register").reply(422, {
      detail: [
        { loc: ["body", "email"], msg: "invalid email" },
        { loc: ["body", "password"], msg: "too short" },
      ],
    });

    await expect(
      registerUser({ email: "x", password: "y" }),
    ).rejects.toBeTruthy();

    expect(toast.error).toHaveBeenCalledWith("invalid email, too short");
  });

  test("не делает refresh на 4xx", async () => {
    mock.onPost("/users/register").reply(400, { detail: "bad" });

    await expect(
      registerUser({ email: "a", password: "b" }),
    ).rejects.toBeTruthy();

    const refreshCalls = mock.history.post.filter(
      (r) => r.url === "/users/refresh",
    );
    expect(refreshCalls).toHaveLength(0);
  });
});

describe("loginUser", () => {
  test("успешный логин возвращает access_token", async () => {
    mock
      .onPost("/users/login")
      .reply(200, { access_token: "abc", token_type: "bearer" });

    const res = await loginUser({ email: "a@a.a", password: "123456" });

    expect(res.access_token).toBe("abc");
    expect(res.token_type).toBe("bearer");
  });

  test("401 (неверный пароль) → не запускает refresh-цикл", async () => {
    mock
      .onPost("/users/login")
      .reply(401, { detail: "Incorrect email or password" });

    await expect(
      loginUser({ email: "a@a.a", password: "wrong" }),
    ).rejects.toBeTruthy();

    expect(toast.error).toHaveBeenCalledWith("Incorrect email or password");
    // ключевая проверка: НЕ дёргаем /users/refresh
    expect(
      mock.history.post.filter((r) => r.url === "/users/refresh"),
    ).toHaveLength(0);
  });
});

describe("refreshTokens", () => {
  test("успешно возвращает новый access_token", async () => {
    mock
      .onPost("/users/refresh")
      .reply(200, { access_token: "new", token_type: "bearer" });

    const res = await refreshTokens();
    expect(res.access_token).toBe("new");
  });

  test("401 пробрасывается, без рекурсии", async () => {
    mock.onPost("/users/refresh").reply(401, { detail: "expired" });

    await expect(refreshTokens()).rejects.toBeTruthy();

    // если бы whitelist не работал — было бы >1 запроса
    expect(
      mock.history.post.filter((r) => r.url === "/users/refresh"),
    ).toHaveLength(1);
  });
});

describe("logoutUser", () => {
  test("возвращает сообщение", async () => {
    mock.onPost("/users/logout").reply(200, { message: "Logged out" });

    const res = await logoutUser();
    expect(res.message).toBe("Logged out");
  });
});

describe("getCurrentUser", () => {
  test("возвращает пользователя", async () => {
    mock.onGet("/users/me").reply(200, { id: 7, email: "me@a.a" });

    const user = await getCurrentUser();
    expect(user).toEqual({ id: 7, email: "me@a.a" });
  });

  test("401 → refresh + успешный retry", async () => {
    mock
      .onGet("/users/me")
      .replyOnce(401)
      .onGet("/users/me")
      .reply(200, { id: 7, email: "me@a.a" });
    mock
      .onPost("/users/refresh")
      .replyOnce(200, { access_token: "new", token_type: "bearer" });

    const user = await getCurrentUser();

    expect(user).toEqual({ id: 7, email: "me@a.a" });
    expect(
      mock.history.post.filter((r) => r.url === "/users/refresh"),
    ).toHaveLength(1);
    expect(mock.history.get.filter((r) => r.url === "/users/me")).toHaveLength(
      2,
    );
  });
});

// ============================================================
// INTERCEPTOR — refresh flow
// ============================================================

describe("axios interceptor: refresh flow", () => {
  test("401 на защищённом эндпоинте → 1 refresh + retry → 200", async () => {
    mock
      .onPost("/projects/create")
      .replyOnce(401)
      .onPost("/projects/create")
      .reply(201, { id: 42 });
    mock
      .onPost("/users/refresh")
      .replyOnce(200, { access_token: "new", token_type: "bearer" });

    const res = await api.post("/projects/create", { name: "P" });

    expect(res.status).toBe(201);
    expect(res.data).toEqual({ id: 42 });
    expect(
      mock.history.post.filter((r) => r.url === "/users/refresh"),
    ).toHaveLength(1);
    expect(
      mock.history.post.filter((r) => r.url === "/projects/create"),
    ).toHaveLength(2);
  });

  test("тело запроса сохраняется при retry", async () => {
    const body = { name: "P", description: "d" };
    mock
      .onPost("/projects/create")
      .replyOnce(401)
      .onPost("/projects/create")
      .reply(201, { id: 1 });
    mock.onPost("/users/refresh").replyOnce(200, { access_token: "new" });

    await api.post("/projects/create", body);

    const calls = mock.history.post.filter((r) => r.url === "/projects/create");
    expect(JSON.parse(calls[0].data)).toEqual(body);
    expect(JSON.parse(calls[1].data)).toEqual(body);
  });

  test("если refresh упал — ошибка пробрасывается, цикла нет", async () => {
    mock.onPost("/projects/create").reply(401);
    mock.onPost("/users/refresh").reply(401);

    await expect(api.post("/projects/create")).rejects.toBeTruthy();

    // create вызван: первый раз + один retry, больше — нет
    expect(
      mock.history.post.filter((r) => r.url === "/projects/create"),
    ).toHaveLength(2);
    // refresh только один, без повторов
    expect(
      mock.history.post.filter((r) => r.url === "/users/refresh"),
    ).toHaveLength(1);
  });

  test("если после успешного refresh retry снова 401 — не рефрешим второй раз", async () => {
    mock.onPost("/projects/create").reply(401); // всегда 401
    mock.onPost("/users/refresh").reply(200, { access_token: "new" });

    await expect(api.post("/projects/create")).rejects.toBeTruthy();

    // _retry защищает от второй попытки refresh
    expect(
      mock.history.post.filter((r) => r.url === "/users/refresh"),
    ).toHaveLength(1);
    expect(
      mock.history.post.filter((r) => r.url === "/projects/create"),
    ).toHaveLength(2); // original + 1 retry
  });

  test("401 на самом /users/refresh — не пытаемся рефрешить refresh (no loop)", async () => {
    mock.onPost("/users/refresh").reply(401);

    await expect(api.post("/users/refresh")).rejects.toBeTruthy();

    expect(
      mock.history.post.filter((r) => r.url === "/users/refresh"),
    ).toHaveLength(1);
  });

  test("N параллельных 401 → ровно один refresh, все ретраятся", async () => {
    let refreshed = false;

    mock.onPost("/users/refresh").reply(() => {
      refreshed = true;
      return [200, { access_token: "new", token_type: "bearer" }];
    });

    mock.onPost("/projects/create").reply(() => {
      if (!refreshed) return [401];
      return [201, { ok: true }];
    });

    const requests = Array.from({ length: 5 }, () =>
      api.post("/projects/create", { name: "P" }),
    );
    const results = await Promise.all(requests);

    expect(results.every((r) => r.status === 201)).toBe(true);
    expect(refreshed).toBe(true);
    // главное: refresh дёрнут РОВНО один раз (работает очередь)
    expect(
      mock.history.post.filter((r) => r.url === "/users/refresh"),
    ).toHaveLength(1);
    // 5 исходных + 5 retry
    expect(
      mock.history.post.filter((r) => r.url === "/projects/create"),
    ).toHaveLength(10);
  });

  test("не трогает не-401 ошибки (403, 422, 500)", async () => {
    mock.onPost("/projects/create").reply(422, { detail: "bad" });
    mock.onPost("/projects/create").reply(500);

    await expect(api.post("/projects/create")).rejects.toBeTruthy();
    await expect(api.post("/projects/create")).rejects.toBeTruthy();

    expect(
      mock.history.post.filter((r) => r.url === "/users/refresh"),
    ).toHaveLength(0);
  });

  test("GET-запросы тоже рефрешатся", async () => {
    mock
      .onGet("/projects")
      .replyOnce(401)
      .onGet("/projects")
      .reply(200, [{ id: 1 }]);
    mock.onPost("/users/refresh").replyOnce(200, { access_token: "new" });

    const res = await api.get("/projects");

    expect(res.data).toEqual([{ id: 1 }]);
    expect(
      mock.history.post.filter((r) => r.url === "/users/refresh"),
    ).toHaveLength(1);
  });
});
