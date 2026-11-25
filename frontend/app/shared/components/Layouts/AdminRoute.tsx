import { useEffect, useState } from "react";
import { Navigate, Outlet } from "react-router-dom";

export function AdminRoute() {
  const [isAdmin, setIsAdmin] = useState<boolean | null>(null);

  useEffect(() => {
    let active = true;

    const checkRole = async () => {
      try {
        if (active) setIsAdmin(localStorage.getItem("role") === "admin");
      } catch {
        if (active) setIsAdmin(false);
      }
    };

    void checkRole();

    return () => {
      active = false;
    };
  }, []);

  if (isAdmin === null) {
    return null;
  }

  return isAdmin ? <Outlet /> : <Navigate to="/projects" replace />;
}
