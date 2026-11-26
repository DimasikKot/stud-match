import { useEffect, useState } from "react";
import { Navigate, Outlet } from "react-router-dom";

export function PrivateRoute() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);

  useEffect(() => {
    let active = true;

    const checkAuth = async () => {
      try {
        if (active)
          setIsAuthenticated(localStorage.getItem("fullname") !== null);
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
