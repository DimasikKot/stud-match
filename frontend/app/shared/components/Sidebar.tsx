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
import { getCurrentUser, logoutUser } from "@/shared/api/users";
import { StatusIndicator } from "@/shared/components/StatusIndicator";
import userIcon from "@/shared/images/circle-user-regular-full.svg";
import { HEALTH_ITEMS, NAV_ITEMS, type HealthKey } from "../constants/sidebar";
import { TextUI } from "./TextUI";
import { IconUI } from "./IconUI";

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
  if (value === undefined) return "-";
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
  const [username, setUsername] = useState<string | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    const loadUser = async () => {
      try {
        const user = await getCurrentUser();
        setUsername(sessionStorage.getItem("fullname"));
        setIsAdmin(user.role === "admin");
      } catch {
        setUsername(null);
        setIsAdmin(false);
      }
    };

    const load = async (
      key: HealthKey,
      request: () => Promise<GetHealthResponse | undefined>,
    ) => {
      const response = await request();
      if (response) {
        setHealth((prev) => ({ ...prev, [key]: response }));
      }
    };

    const loadAll = async () => {
      await loadUser();
      if (sessionStorage.getItem("role") !== "admin") {
        return;
      }

      void load("backend", fetchBackendHealth);
      void load("postgres", fetchPostgresHealth);
      void load("redis", fetchRedisHealth);
      void load("rustfs", fetchRustfsHealth);
      void load("kafka", fetchKafkaHealth);
    };

    void loadAll();
  }, []);

  const handleLogout = async () => {
    try {
      await logoutUser();
    } catch {
      // сессия уже могла истечь
    }

    setUsername(null);
    sessionStorage.removeItem("username");
    sessionStorage.removeItem("email");
    sessionStorage.removeItem("role");
    navigate("/login");
  };

  const iconButtonClass = collapsed
    ? "flex h-5 w-5 text-[#8FCBEA] transition-colors hover:text-white"
    : "flex h-9 w-9 rounded-xl text-[#8FCBEA] transition-colors hover:text-white";
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
          <IconUI
            size="24px"
            icon="menu"
            color="#8FCBEA"
            onClick={onToggle}
            title={collapsed ? "Развернуть меню" : "Свернуть меню"}
            className={iconButtonClass}
          />
          <IconUI
            size="24px"
            icon="logout"
            color="#8FCBEA"
            onClick={handleLogout}
            title="Выйти"
            className={iconButtonClass}
          />
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
            <TextUI variant="normal">
              {collapsed ? shortName : displayName}
            </TextUI>
          </div>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto">
        <div className="flex flex-col">
          {NAV_ITEMS.filter((item) => !item.adminOnly || isAdmin).map(
            (item, index) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `relative flex h-12.5 w-full items-center text-sm font-medium
                  ${collapsed ? "justify-center px-0" : "gap-3 px-6"}
                  ${index > 0 ? "border-t border-white/10" : ""}
                  ${
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
                    <IconUI
                      size="20px"
                      icon={item.icon}
                      color={item.adminOnly ? "red-300" : "white"}
                    />
                    <TextUI
                      className={`${collapsed ? "hidden" : "block font-semibold"} ${item.adminOnly ? "text-red-100" : "text-white"}`}
                    >
                      {item.label}
                    </TextUI>
                  </>
                )}
              </NavLink>
            ),
          )}
        </div>
      </nav>

      {isAdmin && (
        <div
          className={`${
            collapsed ? "hidden" : "hidden lg:block"
          } border-t border-white/10 px-6 py-3`}
        >
          <TextUI variant="subtitle">Система</TextUI>
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
                  <TextUI variant="normal" className="text-white/90">
                    {item.label}
                  </TextUI>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div
        className={`px-6 py-3 text-xs text-white/90 ${
          collapsed ? "hidden" : "block"
        }`}
      >
        <TextUI variant="label">
          GitHub:{" "}
          <a
            href="https://github.com/DimasikKot/stud-match"
            target="_blank"
            rel="noopener noreferrer"
            className="underline decoration-white/40 underline-offset-2 hover:text-white"
          >
            DimasikKot/stud-match
          </a>
        </TextUI>
      </div>
    </aside>
  );
}
