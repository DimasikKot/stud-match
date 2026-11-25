import { useState } from "react";
import { Outlet } from "react-router-dom";

import { Sidebar } from "@/shared/components/Layouts/Sidebar";

export function MainLayout() {
  const [collapsed, setCollapsed] = useState(true);

  return (
    <div className="h-screen bg-white">
      <Sidebar
        collapsed={collapsed}
        onToggle={() => setCollapsed((value) => !value)}
      />
      <main
        className={`w-screen h-screen overflow-y-hidden overflow-x-hidden ${collapsed ? "pl-17" : "pl-68"}`}
      >
        <Outlet />
      </main>
    </div>
  );
}
