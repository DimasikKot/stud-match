import { useEffect, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";

import {
  fetchBackendHealth,
  fetchPostgresHealth,
  fetchRedisHealth,
  fetchRustfsHealth,
  fetchKafkaHealth,
  type GetHealthResponse,
} from "@/shared/api/healths";
import { logoutUser } from "@/shared/api/users";
import { StatusIndicator } from "@/shared/components/StatusIndicator";
import barsIcon from "@/shared/images/bars-solid-full.svg";
import logoutIcon from "@/shared/images/right-from-bracket-solid-full.svg";
import userIcon from "@/shared/images/circle-user-regular-full.svg";

type HealthKey = "backend" | "postgres" | "redis" | "rustfs" | "kafka";

const NAV_ITEMS = [
  { to: "/projects", label: "Проекты", icon: "dashboard" },
  { to: "/files", label: "Файлы", icon: "folder_open" },
  { to: "/llm", label: "Нейросеть", icon: "smart_toy" },
  { to: "/components", label: "Компоненты", icon: "widgets" },
];

const HEALTH_ITEMS: { key: HealthKey; label: string }[] = [
  { key: "backend", label: "Backend" },
  { key: "postgres", label: "Postgres" },
  { key: "redis", label: "Redis" },
  { key: "rustfs", label: "RustFS" },
  { key: "kafka", label: "Kafka" },
];

const SvgIcon = ({
  src,
  className = "",
}: {
  src: string;
  className?: string;
}) => (
  <span
    aria-hidden="true"
    className={`inline-block h-5 w-5 shrink-0 bg-current ${className}`}
    style={{
      maskImage: `url("${src}")`,
      WebkitMaskImage: `url("${src}")`,
      maskSize: "contain",
      WebkitMaskSize: "contain",
      maskRepeat: "no-repeat",
      WebkitMaskRepeat: "no-repeat",
      maskPosition: "center",
      WebkitMaskPosition: "center",
    }}
  />
);

const formatPrimitive = (value: unknown): string => {
  if (value === null) return "null";
  if (value === undefined) return "—";
  if (Array.isArray(value)) return JSON.stringify(value);
  return String(value);
};

const formatMetrics = (metrics?: Record<string, unknown> | null): string => {
  if (!metrics || typeof metrics !== "object") return "";

  const lines: string[] = [];

  const walk = (value: Record<string, unknown>, depth: number) => {
    for (const [key, item] of Object.entries(value)) {
      const pad = "  ".repeat(depth);
      if (item && typeof item === "object" && !Array.isArray(item)) {
        lines.push(`${pad}${key}:`);
        walk(item as Record<string, unknown>, depth + 1);
      } else {
        lines.push(`${pad}${key}: ${formatPrimitive(item)}`);
      }
    }
  };

  walk(metrics, 0);
  return lines.join("\n");
};

export function Sidebar({
  collapsed,
  onToggle,
}: {
  collapsed: boolean;
  onToggle: () => void;
}) {
  const navigate = useNavigate();

  const [health, setHealth] = useState<
    Partial<Record<HealthKey, GetHealthResponse>>
  >({});
  const [username, setUsername] = useState(() =>
    localStorage.getItem("username"),
  );
  const [hasSession, setHasSession] = useState(
    () =>
      Boolean(localStorage.getItem("username")) ||
      Boolean(localStorage.getItem("access_token")),
  );

  useEffect(() => {
    const load = async (
      key: HealthKey,
      request: () => Promise<GetHealthResponse | undefined>,
    ) => {
      const response = await request();
      if (response) {
        setHealth((prev) => ({ ...prev, [key]: response }));
      }
    };

    void load("backend", fetchBackendHealth);
    void load("postgres", fetchPostgresHealth);
    void load("redis", fetchRedisHealth);
    void load("rustfs", fetchRustfsHealth);
    void load("kafka", fetchKafkaHealth);
  }, []);

  const handleLogout = async () => {
    if (hasSession) {
      try {
        await logoutUser();
      } catch {
        // сессия уже могла истечь
      }
    }

    localStorage.removeItem("username");
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUsername(null);
    setHasSession(false);
    navigate("/projects");
  };

  const iconButtonClass = collapsed
    ? "flex h-5 w-5 items-center justify-center text-[#8FCBEA] transition-colors hover:text-white"
    : "flex h-9 w-9 items-center justify-center rounded-xl text-[#8FCBEA] transition-colors hover:text-white";
  const displayName = username ?? "Гость";
  const nameParts =
    username
      ?.replace(/@.*/, "")
      .trim()
      .split(/[\s._-]+/)
      .filter(Boolean) ?? [];
  const shortName = nameParts.length
    ? `${nameParts
        .slice(0, 2)
        .map((part) => part[0]?.toUpperCase())
        .join(".")}.`
    : "Г";

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-40 flex flex-col bg-[#238BC8] text-white ${
        collapsed ? "w-17" : "w-68"
      }`}
    >
      <div className="px-6 py-6">
        <div
          className={`flex items-center gap-2 ${
            collapsed ? "-mx-2 gap-4 flex-col" : "-m-2 justify-between"
          }`}
        >
          <button
            type="button"
            onClick={onToggle}
            title={collapsed ? "Развернуть меню" : "Свернуть меню"}
            aria-label={collapsed ? "Развернуть меню" : "Свернуть меню"}
            className={iconButtonClass}
          >
            <SvgIcon src={barsIcon} className="h-6 w-6" />
          </button>
          <button
            type="button"
            onClick={handleLogout}
            title="Выйти"
            aria-label="Выйти"
            className={iconButtonClass}
          >
            <SvgIcon src={logoutIcon} className="h-6 w-6" />
          </button>
        </div>

        <div className="mt-4 flex flex-col items-center gap-1.5">
          <SvgIcon
            src={userIcon}
            className={`text-white ${collapsed ? "h-8 w-8" : "h-17 w-17"}`}
          />
          <div
            className={`text-center text-sm font-semibold ${
              collapsed ? "whitespace-nowrap" : "w-full truncate"
            }`}
          >
            {collapsed ? shortName : displayName}
          </div>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto">
        <div className="flex flex-col">
          {NAV_ITEMS.map((item, index) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `relative flex h-12.5 w-full items-center text-sm font-medium ${
                  collapsed ? "justify-center px-0" : "gap-3 px-6"
                } ${index > 0 ? "border-t border-white/10" : ""} ${
                  isActive
                    ? "bg-[#f98941] text-white"
                    : "text-white/90 hover:text-white"
                }`
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <span className="absolute left-0 top-0 h-full w-1 bg-[#CE6327]" />
                  )}
                  <span
                    className="material-icons leading-none text-white"
                    style={{ fontSize: "20px", lineHeight: 1 }}
                  >
                    {item.icon}
                  </span>
                  <span
                    className={collapsed ? "hidden" : "block font-semibold"}
                  >
                    {item.label}
                  </span>
                </>
              )}
            </NavLink>
          ))}
        </div>
      </nav>

      <div
        className={`${
          collapsed ? "hidden" : "hidden lg:block"
        } border-t border-white/10 px-4 py-3`}
      >
        <div className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-white/70">
          Система
        </div>
        <div className="flex flex-col gap-1.5">
          {HEALTH_ITEMS.map((item) => {
            const status = health[item.key];
            return (
              <div
                key={item.key}
                className="flex items-center gap-2"
                title={formatMetrics(status?.metrics)}
              >
                <StatusIndicator status={status?.success} />
                <span className="text-xs text-white/90">{item.label}</span>
              </div>
            );
          })}
        </div>
      </div>

      <div
        className={`px-6 py-3 text-xs text-white/90 ${
          collapsed ? "hidden" : "block"
        }`}
      >
        <p>
          GitHub:{" "}
          <a
            href="https://github.com/DimasikKot/stud-match"
            target="_blank"
            rel="noopener noreferrer"
            className="underline decoration-white/40 underline-offset-2 hover:text-white"
          >
            DimasikKot/stud-match
          </a>
        </p>
      </div>
    </aside>
  );
}
