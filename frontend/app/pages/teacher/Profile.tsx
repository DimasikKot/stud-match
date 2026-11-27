import { useEffect, useState } from "react";
import toast from "react-hot-toast";

import {
  changePassword,
  getCurrentUser,
  type UserResponse,
} from "@/shared/api/users";
import { PageLayout } from "@/shared/components/Layouts/PageLayout";
import { ButtonUI } from "@/shared/components/UI/ButtonUI";
import { InputUI } from "@/shared/components/UI/InputUI";
import { TextUI } from "@/shared/components/UI/TextUI";
import { skillsSetToLevels } from "@/shared/utils/skillsSet";

const ROLE_LABELS: Record<string, string> = {
  admin: "Администратор",
  teacher: "Преподаватель",
};

export default function Profile() {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    getCurrentUser()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setIsLoading(false));
  }, []);

  const handleChangePassword = async () => {
    if (!oldPassword || !newPassword) {
      toast.error("Заполните все поля");
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error("Новые пароли не совпадают");
      return;
    }

    setIsSaving(true);
    try {
      await changePassword({
        old_password: oldPassword,
        new_password: newPassword,
      });
      toast.success("Пароль изменён");
      setOldPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch {
      // Ошибка уже показана через errorValidate
    } finally {
      setIsSaving(false);
    }
  };

  const skillNames = Object.entries(skillsSetToLevels(user?.skills_set)).map(
    ([name, level]) => `${name} (${level})`,
  );

  return (
    <PageLayout title="Профиль">
      {isLoading ? (
        <div className="bg-white border border-gray-300 text-center">
          <TextUI variant="desc">Загрузка...</TextUI>
        </div>
      ) : user === null ? (
        <div className="bg-white border border-gray-300 text-center">
          <TextUI variant="desc">Не удалось загрузить профиль</TextUI>
        </div>
      ) : (
        <div className="flex flex-col gap-6 max-w-xl">
          <div className="bg-white border border-gray-300 p-4">
            <TextUI variant="subtitle" className="mb-3">
              Информация
            </TextUI>

            <div className="flex flex-col gap-2">
              <TextUI variant="label">ФИО</TextUI>
              <TextUI variant="normal">{user.fullname}</TextUI>

              <TextUI variant="label" className="mt-2">
                Почта
              </TextUI>
              <TextUI variant="normal">{user.email}</TextUI>

              <TextUI variant="label" className="mt-2">
                Роль
              </TextUI>
              <TextUI variant="normal">
                {ROLE_LABELS[user.role] ?? user.role}
              </TextUI>

              <TextUI variant="label" className="mt-2">
                Навыки
              </TextUI>
              <TextUI variant="normal">
                {skillNames.length > 0 ? skillNames.join(", ") : "Не указаны"}
              </TextUI>
            </div>
          </div>

          <div className="bg-white border border-gray-300 p-4">
            <TextUI variant="subtitle" className="mb-3">
              Смена пароля
            </TextUI>

            <div className="flex flex-col gap-3">
              <InputUI
                value={oldPassword}
                setValue={setOldPassword}
                type="password"
                name="old_password"
                placeholder="Текущий пароль"
              />
              <InputUI
                value={newPassword}
                setValue={setNewPassword}
                type="password"
                name="new_password"
                placeholder="Новый пароль"
              />
              <InputUI
                value={confirmPassword}
                setValue={setConfirmPassword}
                type="password"
                name="confirm_password"
                placeholder="Повторите новый пароль"
                onEnter={handleChangePassword}
              />

              <ButtonUI onClick={handleChangePassword} disabled={isSaving}>
                {isSaving ? "Сохранение..." : "Сменить пароль"}
              </ButtonUI>
            </div>
          </div>
        </div>
      )}
    </PageLayout>
  );
}
