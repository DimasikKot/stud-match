import { useEffect, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";

import illustration from "@/shared/images/illustration.jpg";
import logo from "@/shared/images/logo.png";

import { ButtonUI } from "@/shared/components/UI/ButtonUI";
import { InputUI } from "@/shared/components/UI/InputUI";
import { TextUI } from "@/shared/components/UI/TextUI";

import { getCurrentUser, loginUser } from "@/shared/api/users";

export function Login() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);

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

  const handleLogin = async () => {
    if (!email || !password) {
      toast.error("Введите почту и пароль");
      return;
    }

    setIsLoading(true);
    try {
      await loginUser({ email, password });
      navigate("/", { replace: true });
    } catch {
      // Ошибка уже показана через errorValidate
    } finally {
      setIsLoading(false);
    }
  };

  return isAuthenticated ? (
    <Navigate to="/" replace />
  ) : (
    <div className="relative min-h-screen w-full overflow-hidden">
      <img
        src={illustration}
        alt=""
        className="absolute inset-0 h-full w-full object-cover"
      />
      <div className="absolute inset-x-0 bottom-0 h-5 bg-gray-400" />

      <div className="relative flex min-h-screen items-center justify-center p-6">
        <div className="flex w-107.5 max-w-full flex-col gap-4 border border-gray-300 bg-white p-8">
          <img
            src={logo}
            alt="StudMatch"
            className="mx-auto h-16 p-0.5 w-auto"
          />

          <TextUI variant="title">Вход</TextUI>

          <InputUI
            value={email}
            setValue={setEmail}
            type="email"
            name="email"
            placeholder="Почта"
            autoFocus
          />

          <InputUI
            value={password}
            setValue={setPassword}
            type="password"
            name="password"
            placeholder="Пароль"
            onEnter={handleLogin}
          />

          <ButtonUI
            onClick={handleLogin}
            disabled={isLoading}
            className="w-full"
          >
            {isLoading ? "Вход..." : "Войти"}
          </ButtonUI>
        </div>
      </div>
    </div>
  );
}
