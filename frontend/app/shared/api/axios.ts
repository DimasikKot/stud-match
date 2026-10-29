import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import toast from "react-hot-toast";

const BACKEND_URL =
  import.meta.env.VITE_BACKEND_URL ?? "https://localhost/backend/api/v1";

// Создаём инстанс Axios
// withCredentials: true — access_token и refresh_token живут в httpOnly-куках,
// браузер сам приложит их к каждому запросу. JS к ним доступа не имеет (XSS-safe).
const api = axios.create({
  baseURL: BACKEND_URL,
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
});

// ===== Автообновление access-токена с очередью =====
type RetryConfig = InternalAxiosRequestConfig & { _retry?: boolean };

let isRefreshing = false;
let pendingQueue: Array<(ok: boolean) => void> = [];

const processQueue = (ok: boolean) => {
  pendingQueue.forEach((resolve) => resolve(ok));
  pendingQueue = [];
};

// На эти эндпоинты не вешаем refresh-retry:
// - /users/refresh — чтобы не было рекурсии
// - /users/login, /users/register — 401 = неверные креды, refresh не поможет
// - /users/logout — нечего рефрешить
const REFRESH_WHITELIST = [
  "/users/refresh",
  "/users/login",
  "/users/register",
  "/users/logout",
];

const isWhitelisted = (url?: string) =>
  !!url && REFRESH_WHITELIST.some((path) => url.includes(path));

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as RetryConfig | undefined;

    // Не 401, нет конфига, уже ретраили или whitelisted — просто пробрасываем
    if (
      error.response?.status !== 401 ||
      !original ||
      original._retry ||
      isWhitelisted(original.url)
    ) {
      return Promise.reject(error);
    }

    // Пока идёт refresh — ставим параллельные запросы в очередь,
    // чтобы не дёргать /users/refresh несколько раз одновременно
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        pendingQueue.push((ok) => {
          if (ok) {
            original._retry = true;
            resolve(api(original));
          } else {
            reject(error);
          }
        });
      });
    }

    original._retry = true;
    isRefreshing = true;

    try {
      // refresh_token берётся из httpOnly-куки автоматически
      await api.post("/users/refresh");
      processQueue(true);
      return api(original);
    } catch (refreshError) {
      processQueue(false);
      toast.error("Сессия истекла, войдите заново");
      // window.location.href = "/login";
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  },
);

export const errorValidate = (error: unknown) => {
  if (axios.isAxiosError(error)) {
    let error_text = "Ошибка при загрузке файла";

    if (error.response?.data?.detail) {
      const detail = error.response.data.detail;

      // Массив ошибок валидации FastAPI
      if (Array.isArray(detail)) {
        error_text = detail.map((err) => err.msg || err.message).join(", ");
      }
      // Строка
      else if (typeof detail === "string") {
        error_text = detail;
      }
      // Объект с msg
      else if (detail?.msg) {
        error_text = detail.msg;
      }
      // Иначе — строковое представление
      else {
        error_text = String(detail);
      }
    } else if (error.message) {
      error_text = `Ошибка ${error.message}`;
    }

    toast.error(error_text);
  }
};

export default api;
