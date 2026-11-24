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
import { StatusUI } from "@/shared/components/UI/StatusUI";
import { TooltipUI } from "@/shared/components/UI/TooltipUI";
import userIcon from "@/shared/images/circle-user-regular-full.svg";
import {
  HEALTH_ITEMS,
  NAV_ITEMS,
  type HealthKey,
} from "@/shared/constants/sidebar";
import { TextUI } from "@/shared/components/UI/TextUI";
import { IconUI } from "@/shared/components/UI/IconUI";
import { IconSvgUI } from "@/shared/components/UI/IconSvgUI";

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
  const [fullname, setFullname] = useState<string | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    const loadUser = async () => {
      try {
        const user = await getCurrentUser();
        setFullname(sessionStorage.getItem("fullname"));
        setIsAdmin(user.role === "admin");
      } catch {
        setFullname(null);
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

    setFullname(null);
    sessionStorage.removeItem("fullname");
    sessionStorage.removeItem("email");
    sessionStorage.removeItem("role");
    navigate("/login");
  };

  const displayName = fullname ?? "Гость";
  const nameParts =
    fullname
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
          className={`flex items-center -mx-0.5 ${
            collapsed ? "gap-3 flex-col" : "justify-between"
          }`}
        >
          <IconUI
            icon="menu"
            size="24px"
            onClick={onToggle}
            title={collapsed ? "Развернуть меню" : "Свернуть меню"}
            className={`flex items-center justify-center text-[#8FCBEA] transition-colors hover:text-white`}
          />

          <IconUI
            icon="logout"
            size="24px"
            onClick={handleLogout}
            title="Выйти"
            className={`flex items-center justify-center text-[#8FCBEA] transition-colors hover:text-white`}
          />
        </div>

        <div className="mt-4 flex flex-col items-center gap-1.5">
          <IconSvgUI
            src={userIcon}
            className={`text-white ${collapsed ? "w-8 h-8" : "w-17 h-17"}`}
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

      <nav className="flex-1">
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
                      <div className="absolute left-0 top-0 h-full w-1 bg-[#CE6327]" />
                    )}

                    <IconUI
                      icon={item.icon}
                      size="20px"
                      color={`flex items-center justify-center ${item.adminOnly ? "text-red-300" : "text-white"}`}
                    />

                    {collapsed ? null : (
                      <TextUI
                        variant="normal"
                        className={
                          item.adminOnly ? "text-red-100" : "text-white"
                        }
                      >
                        {item.label}
                      </TextUI>
                    )}
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
                <TooltipUI
                  key={item.key}
                  content={status?.metrics}
                  isJSON
                  className="flex items-center gap-2 w-fit"
                >
                  <StatusUI status={status?.success} title={item.label} />
                </TooltipUI>
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
