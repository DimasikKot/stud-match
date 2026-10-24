import { Navigate, Outlet } from "react-router-dom";

export function PrivateRoute() {
  const token = localStorage.getItem("access_token");

  return token ? <Outlet /> : <Navigate to="/login" replace />;
}
