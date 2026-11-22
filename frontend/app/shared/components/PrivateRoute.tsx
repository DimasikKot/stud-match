import { useEffect, useState } from "react";
import { Navigate, Outlet } from "react-router-dom";

import { getCurrentUser } from "@/shared/api/users";

export function PrivateRoute() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);

  useEffect(() => {
    let active = true;

    const checkAuth = async () => {
      try {
        await getCurrentUser();
        if (active) setIsAuthenticated(true);
      } catch {
        if (active) setIsAuthenticated(false);
      }
    };

    void checkAuth();

    return () => {
      active = false;
    };
  }, []);

  if (isAuthenticated === null) {
    return null;
  }

  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
}
