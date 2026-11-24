export const NAV_ITEMS: {
  to: string;
  label: string;
  icon: string;
  adminOnly?: boolean;
}[] = [
  { to: "/projects", label: "Проекты", icon: "dashboard" }, // + создание и редактирование
  { to: "/students", label: "Студенты", icon: "school" }, // + просмотр студентов
  { to: "/teachers", label: "Преподаватели", icon: "group" }, // + создание и редактирование для админа
  {
    to: "/distributions",
    label: "Распределения",
    icon: "account_tree_outlined",
  }, // + создание и запуск
  { to: "/profile", label: "Профиль", icon: "person" }, // редактирование профиля
  {
    to: "/files",
    label: "Файлы студентов",
    icon: "folder_open",
    adminOnly: true,
  }, // + загрузка и удаление для админа
  { to: "/components", label: "Компоненты", icon: "code", adminOnly: true },
];

export type HealthKey = "backend" | "postgres" | "redis" | "rustfs" | "kafka";

export const HEALTH_ITEMS: { key: HealthKey; label: string }[] = [
  { key: "backend", label: "Backend" },
  { key: "postgres", label: "Postgres" },
  { key: "redis", label: "Redis" },
  { key: "rustfs", label: "RustFS" },
  { key: "kafka", label: "Kafka" },
];
