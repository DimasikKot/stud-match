import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import "material-icons/iconfont/material-icons.css";

import { ToasterUI } from "@/shared/components/ToasterUI";
import { PrivateRoute } from "@/shared/components/PrivateRoute";

import { Home } from "@/pages/main/Home";
import { NotFound } from "@/pages/main/NotFound";
import { Components } from "@/pages/main/Components";

export function App() {
  return (
    <Router>
      <ToasterUI />

      <div className="bg-white">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="*" element={<NotFound />} />
          <Route path="/components" element={<Components />} />

          {/* <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} /> */}

          {/* Защищенные маршруты, пересылает на страницу `/login` */}
          <Route element={<PrivateRoute />}>
          </Route>
        </Routes>
      </div>
    </Router>
  );
}
