import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Menu, MenuButton, MenuItem, MenuItems } from "@headlessui/react";

import logo from "@/shared/images/logo.svg";
import { StatusIndicator } from "@/shared/components/StatusIndicator";
import { ButtonUI } from "@/shared/components/ButtonUI";
import { fetchBackendHealth } from "@/shared/api/health";
import { TextUI } from "@/shared/components/TextUI";

const Logo = ({ onClick }: { onClick?: () => void }) => (
  <div onClick={onClick} className="w-full lg:w-auto h-14">
    <div className="flex items-center hover:bg-gray-400/30 transition duration-200 gap-2 w-max cursor-pointer p-1 rounded-xl">
      <img src={logo} alt="React logo" className="select-none" />
      <TextUI variant="logo" className="mb-1">
        Лаборатория разметки
      </TextUI>
    </div>
  </div>
);

const UserIcon = ({ username }: { username: string }) => (
  <div
    className="w-12 h-12 rounded-full bg-linear-to-br select-none
    from-blue-500 to-indigo-600 text-white font-semibold flex items-center justify-center
    shadow-md hover:shadow-lg transition-all hover:scale-105 active:scale-95 cursor-pointer"
  >
    {username[0].toUpperCase()}
  </div>
);

export function Header({
  title,
  className,
  children,
}: {
  title?: string;
  className?: string;
  children?: React.ReactNode;
}) {
  const navigate = useNavigate();

  const [backendStatus, setBackendStatus] = useState(false);
  const username = localStorage.getItem("username");

  useEffect(() => {
    const load = async () => {
      const dataBackend = await fetchBackendHealth();
      if (dataBackend === undefined) return;
      setBackendStatus(dataBackend.success);
    };

    load();
  }, []);

  return (
    <div
      className={`w-full flex flex-col lg:flex-row lg:items-center lg:justify-between
        p-1 gap-4 sticky top-0 self-start border border-b border-gray-200 bg-white z-50 ${className}`}
    >
      <Logo onClick={() => navigate("/")} />

      {title && (
        <TextUI
          variant="header"
          maxLines={1}
          className={`w-full lg:flex-1 text-center`}
        >
          {title}
        </TextUI>
      )}

      {children}

      <div className="flex flex-col sm:flex-row items-center justify-between lg:justify-end gap-4 w-full lg:w-auto">
        {/* Индикаторы состояния контейнеров */}
        <div className="flex gap-4">
          <div className="flex flex-wrap items-center justify-center gap-3">
            <StatusIndicator status={backendStatus} />
            <TextUI variant="desc" isSpan>
              Backend
            </TextUI>
          </div>
        </div>

        {/* Кнопки входа и регистрации */}
        <div className="flex items-center gap-2">
          <ButtonUI onClick={() => navigate("/components")}>
            Компоненты
          </ButtonUI>

          {username ? (
            <Menu as="div" className="relative">
              {/* Кнопка */}
              <MenuButton className="outline-none">
                <UserIcon username={username} />
              </MenuButton>

              {/* Меню */}
              <MenuItems
                className="absolute right-0 mt-3 px-4 py-3 w-56 flex flex-col items-start
                          gap-2 bg-white rounded-2xl shadow-xl border border-gray-300 z-100 focus:outline-none"
              >
                <TextUI isSelectable>{username}</TextUI>

                <div className="w-full border-b border-gray-300" />

                <MenuItem>
                  <ButtonUI
                    onClick={() => navigate("/profile")}
                    variant="link"
                    className={`text-red-600 hover:text-red-800 w-full z-10`}
                  >
                    <TextUI>Выход</TextUI>
                  </ButtonUI>
                </MenuItem>
              </MenuItems>
            </Menu>
          ) : (
            <ButtonUI onClick={() => navigate("/login")}>Войти</ButtonUI>
          )}
        </div>
      </div>
    </div>
  );
}
