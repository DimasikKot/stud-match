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

import { Projects } from "@/pages/main/Projects";
import { NotFound } from "@/pages/main/NotFound";
import { Components } from "@/pages/main/Components";
import { Files } from "@/pages/main/Files";
import { Llm } from "@/pages/main/Llm";

import { Login } from "@/pages/main/Login";
import { Register } from "@/pages/main/Register";

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
              <Route path="/components" element={<Components />} />
              <Route path="/files" element={<Files />} />
              <Route path="/llm" element={<Llm />} />
              <Route path="/register" element={<Register />} />
            </Route>
          </Route>
        </Routes>
      </div>
    </Router>
  );
}
