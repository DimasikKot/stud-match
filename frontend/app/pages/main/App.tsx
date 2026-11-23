import {
  BrowserRouter as Router,
  Route,
  Routes,
  Navigate,
} from "react-router-dom";
import "material-icons/iconfont/material-icons.css";

import { ToasterUI } from "@/shared/components/ToasterUI";
import { MainLayout } from "@/shared/components/MainLayout";
import { PrivateRoute } from "@/shared/components/PrivateRoute";
import { AdminRoute } from "@/shared/components/AdminRoute";

import { Login } from "@/pages/main/Login";

import { Projects } from "@/pages/main/Projects";
import { NotFound } from "@/pages/main/NotFound";

import Students from "@/pages/main/Students";
import Teachers from "@/pages/main/Teachers";
import Matches from "@/pages/main/Matches";
import Profile from "@/pages/main/Profile";

import { Files } from "@/pages/main/Files";
import { Components } from "@/pages/main/Components";

export function App() {
  return (
    <Router>
      <ToasterUI />

      <div className="bg-white">
        <Routes>
          <Route path="/login" element={<Login />} />

          {/* Защищенные маршруты, пересылает на страницу `/login` */}
          <Route element={<PrivateRoute />}>
            <Route element={<MainLayout />}>
              <Route path="*" element={<NotFound />} />
              <Route path="/" element={<Navigate to="/projects" replace />} />
              <Route path="/projects" element={<Projects />} />
              <Route path="/students" element={<Students />} />
              <Route path="/teachers" element={<Teachers />} />
              <Route path="/matches" element={<Matches />} />
              <Route path="/profile" element={<Profile />} />
              <Route element={<AdminRoute />}>
                <Route path="/files" element={<Files />} />
                <Route path="/components" element={<Components />} />
              </Route>
            </Route>
          </Route>
        </Routes>
      </div>
    </Router>
  );
}
