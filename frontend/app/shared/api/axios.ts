import axios from "axios";
import toast from "react-hot-toast";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

// Создаём инстанс Axios
const api = axios.create({
  baseURL: BACKEND_URL,
  withCredentials: true, // Если сервер использует куки
  headers: { "Content-Type": "application/json" },
});

// Интерцептор запросов (автоматически добавляет токен)
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Интерцептор ответов (обрабатывает 401 и обновляет токен)
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token"); // Удаляем токен, если невалидный
      localStorage.removeItem("username");
      // window.location.href = "/login"; // Редирект на страницу входа
    }
    return Promise.reject(error);
  },
);

export const errorValidate = (error: unknown) => {
  if (axios.isAxiosError(error)) {
    let error_text = "Ошибка при загрузке файла";

    if (error.response?.data?.detail) {
      const detail = error.response.data.detail;

      // Если detail - массив ошибок валидации
      if (Array.isArray(detail)) {
        error_text = detail.map((err) => err.msg || err.message).join(", ");
      }
      // Если detail - строка
      else if (typeof detail === "string") {
        error_text = detail;
      }
      // Если detail - объект с полем msg
      else if (detail?.msg) {
        error_text = detail.msg;
      }
      // Иначе строковое представление
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
