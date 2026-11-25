import {
  BrowserRouter as Router,
  Route,
  Routes,
  Navigate,
} from "react-router-dom";
import "material-icons/iconfont/material-icons.css";

import { ToasterLayout } from "@/shared/components/Layouts/ToasterLayout";
import { MainLayout } from "@/shared/components/Layouts/MainLayout";
import { PrivateRoute } from "@/shared/components/Layouts/PrivateRoute";
import { AdminRoute } from "@/shared/components/Layouts/AdminRoute";

import { Login } from "@/pages/main/Login";

import { Projects } from "@/pages/teacher/Projects";
import { NotFound } from "@/pages/main/NotFound";

import Students from "@/pages/teacher/Students";
import Teachers from "@/pages/teacher/Teachers";
import Distributions from "@/pages/teacher/Distributions";
import Profile from "@/pages/teacher/Profile";

import { Files } from "@/pages/teacher/Files";
import { ZipFiles } from "@/pages/teacher/ZipFiles";
import { Components } from "@/shared/components/UI/Components";

export function App() {
  return (
    <Router>
      <ToasterLayout />

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
              <Route path="/distributions" element={<Distributions />} />
              <Route path="/profile" element={<Profile />} />
              <Route element={<AdminRoute />}>
                <Route path="/files" element={<Files />} />
                <Route path="/files/zips/:zipId" element={<ZipFiles />} />
                <Route path="/components" element={<Components />} />
              </Route>
            </Route>
          </Route>
        </Routes>
      </div>
    </Router>
  );
}
