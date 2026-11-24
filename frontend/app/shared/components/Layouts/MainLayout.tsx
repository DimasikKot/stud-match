import { useState } from "react";
import { Outlet } from "react-router-dom";

import { Sidebar } from "@/shared/components/Layouts/Sidebar";

export function MainLayout() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="min-h-screen bg-white">
      <Sidebar
        collapsed={collapsed}
        onToggle={() => setCollapsed((value) => !value)}
      />
      <main className={`min-h-screen ${collapsed ? "pl-17" : "pl-68"}`}>
        <Outlet />
      </main>
    </div>
  );
}
