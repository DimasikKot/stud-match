import { useEffect, useState } from "react";
import toast from "react-hot-toast";

import {
  createSkill,
  deleteSkill,
  fetchSkills,
  type SkillResponse,
} from "@/shared/api/skills";
import {
  fetchUsers,
  getCurrentUser,
  registerUser,
  updateUser,
  type UserResponse,
} from "@/shared/api/users";
import { PageLayout } from "@/shared/components/Layouts/PageLayout";
import { ButtonUI } from "@/shared/components/UI/ButtonUI";
import { IconUI } from "@/shared/components/UI/IconUI";
import { InputUI } from "@/shared/components/UI/InputUI";
import { TextUI } from "@/shared/components/UI/TextUI";
import { SkillsPicker } from "@/shared/components/SkillsPicker";
import { skillsSetToLevels } from "@/shared/utils/skillsSet";

const ROLE_LABELS: Record<string, string> = {
  admin: "Администратор",
  teacher: "Преподаватель",
};

const emptyTeacherForm = {
  fullname: "",
  email: "",
  password: "",
};

export default function Teachers() {
  const [users, setUsers] = useState<UserResponse[]>([]);
  const [skills, setSkills] = useState<SkillResponse[]>([]);
  const [isAdmin, setIsAdmin] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [teacherForm, setTeacherForm] = useState(emptyTeacherForm);
  const [isSaving, setIsSaving] = useState(false);

  const [newSkillName, setNewSkillName] = useState("");

  const [editingUser, setEditingUser] = useState<UserResponse | null>(null);
  const [editForm, setEditForm] = useState({
    fullname: "",
    email: "",
    role: "teacher",
    skillLevels: {} as Record<string, number>,
  });

  const loadSkills = () =>
    fetchSkills()
      .then((response) => setSkills(response.data))
      .catch(() => setSkills([]));

  useEffect(() => {
    Promise.all([
      fetchUsers()
        .then((response) => setUsers(response.data))
        .catch(() => setHasError(true)),
      loadSkills(),
      getCurrentUser()
        .then((user) => setIsAdmin(user.role === "admin"))
        .catch(() => setIsAdmin(false)),
    ]).finally(() => setIsLoading(false));
  }, []);

  const handleCreateTeacher = async () => {
    if (!teacherForm.fullname || !teacherForm.email || !teacherForm.password) {
      toast.error("Заполните все поля");
      return;
    }

    setIsSaving(true);
    try {
      await registerUser({
        fullname: teacherForm.fullname,
        email: teacherForm.email,
        password: teacherForm.password,
      });
      toast.success("Преподаватель создан");
      setTeacherForm(emptyTeacherForm);
      setShowCreateForm(false);
      const response = await fetchUsers();
      setUsers(response.data);
    } catch {
      // Ошибка уже показана через errorValidate
    } finally {
      setIsSaving(false);
    }
  };

  const handleAddSkill = async () => {
    const name = newSkillName.trim();
    if (!name) {
      toast.error("Введите название навыка");
      return;
    }

    try {
      const created = await createSkill(name);
      setSkills((prev) =>
        [...prev, created].sort((a, b) => a.name.localeCompare(b.name)),
      );
      setNewSkillName("");
      toast.success("Навык добавлен");
    } catch {
      // Ошибка уже показана через errorValidate
    }
  };

  const handleDeleteSkill = async (skillId: number) => {
    try {
      await deleteSkill(skillId);
      setSkills((prev) => prev.filter((skill) => skill.id !== skillId));
      toast.success("Навык удалён");
    } catch {
      // Ошибка уже показана через errorValidate
    }
  };

  const startEdit = (user: UserResponse) => {
    setEditingUser(user);
    setEditForm({
      fullname: user.fullname,
      email: user.email,
      role: user.role,
      skillLevels: skillsSetToLevels(user.skills_set),
    });
  };

  const handleSaveEdit = async () => {
    if (!editingUser) return;
    if (!editForm.fullname || !editForm.email) {
      toast.error("Заполните все поля");
      return;
    }

    setIsSaving(true);
    try {
      const updated = await updateUser(editingUser.id, {
        fullname: editForm.fullname,
        email: editForm.email,
        role: editForm.role,
        skills_set: editForm.skillLevels,
      });
      setUsers((prev) =>
        prev.map((user) => (user.id === updated.id ? updated : user)),
      );
      toast.success("Профиль обновлён");
      setEditingUser(null);
    } catch {
      // Ошибка уже показана через errorValidate
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <PageLayout title="Преподаватели">
      <TextUI variant="header" className="mb-4">
        Преподаватели ({users.length})
      </TextUI>

      {isAdmin && (
        <>
          <div className="bg-white border border-gray-300 p-4 mb-6">
            <div className="grid grid-cols-2 items-center justify-between mb-3">
              <TextUI variant="subtitle">Словарь навыков</TextUI>
              <ButtonUI
                variant="secondary"
                onClick={() => setShowCreateForm((prev) => !prev)}
              >
                {showCreateForm ? "Скрыть форму" : "Добавить преподавателя"}
              </ButtonUI>
            </div>

            <div className="grid grid-cols-2 gap-2 mb-3">
              <InputUI
                value={newSkillName}
                setValue={setNewSkillName}
                placeholder="Название навыка"
                onEnter={handleAddSkill}
              />
              <ButtonUI onClick={handleAddSkill} className="w-32 shrink-0">
                Добавить
              </ButtonUI>
            </div>

            {skills.length === 0 ? (
              <TextUI variant="desc">Навыков пока нет</TextUI>
            ) : (
              <div className="flex flex-wrap gap-2">
                {skills.map((skill) => (
                  <span
                    key={skill.id}
                    className="inline-flex items-center gap-1 border border-gray-300 px-2 py-0.5"
                  >
                    <TextUI variant="label" span>
                      {skill.name}
                    </TextUI>
                    <IconUI
                      name="close"
                      size="16px"
                      onClick={() => handleDeleteSkill(skill.id)}
                      title="Удалить навык"
                      className="cursor-pointer text-gray-500 hover:text-gray-800"
                    />
                  </span>
                ))}
              </div>
            )}
          </div>

          {showCreateForm && (
            <div className="bg-white border border-gray-300 p-4 mb-6">
              <TextUI variant="subtitle" className="mb-3">
                Новый преподаватель
              </TextUI>
              <div className="flex flex-col gap-3 max-w-md">
                <InputUI
                  value={teacherForm.fullname}
                  onChange={(event) =>
                    setTeacherForm((prev) => ({
                      ...prev,
                      fullname: event.target.value,
                    }))
                  }
                  placeholder="ФИО"
                />
                <InputUI
                  value={teacherForm.email}
                  onChange={(event) =>
                    setTeacherForm((prev) => ({
                      ...prev,
                      email: event.target.value,
                    }))
                  }
                  type="email"
                  placeholder="Почта"
                />
                <InputUI
                  value={teacherForm.password}
                  onChange={(event) =>
                    setTeacherForm((prev) => ({
                      ...prev,
                      password: event.target.value,
                    }))
                  }
                  type="password"
                  placeholder="Пароль"
                  onEnter={handleCreateTeacher}
                />
                <ButtonUI onClick={handleCreateTeacher} disabled={isSaving}>
                  {isSaving ? "Создание..." : "Создать"}
                </ButtonUI>
              </div>
            </div>
          )}
        </>
      )}

      {isLoading ? (
        <div className="bg-white border border-gray-300 text-center">
          <TextUI variant="desc">Загрузка...</TextUI>
        </div>
      ) : hasError ? (
        <div className="bg-white border border-gray-300 text-center">
          <TextUI variant="desc">
            Не удалось загрузить список преподавателей
          </TextUI>
        </div>
      ) : users.length === 0 ? (
        <div className="bg-white border border-gray-300 text-center">
          <TextUI variant="desc">Преподавателей пока нет</TextUI>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {users.map((user) =>
            editingUser?.id === user.id ? (
              <div
                key={user.id}
                className="bg-white border border-gray-300 p-4 flex flex-col gap-3"
              >
                <TextUI variant="subtitle">Редактирование</TextUI>

                <InputUI
                  value={editForm.fullname}
                  onChange={(event) =>
                    setEditForm((prev) => ({
                      ...prev,
                      fullname: event.target.value,
                    }))
                  }
                  placeholder="ФИО"
                />
                <InputUI
                  value={editForm.email}
                  onChange={(event) =>
                    setEditForm((prev) => ({
                      ...prev,
                      email: event.target.value,
                    }))
                  }
                  type="email"
                  placeholder="Почта"
                />

                <div className="flex gap-2">
                  {(["teacher", "admin"] as const).map((role) => (
                    <ButtonUI
                      key={role}
                      variant={editForm.role === role ? "primary" : "secondary"}
                      onClick={() => setEditForm((prev) => ({ ...prev, role }))}
                      className="flex-1"
                    >
                      {ROLE_LABELS[role]}
                    </ButtonUI>
                  ))}
                </div>

                <SkillsPicker
                  skills={skills}
                  value={editForm.skillLevels}
                  onChange={(levels) =>
                    setEditForm((prev) => ({ ...prev, skillLevels: levels }))
                  }
                />

                <div className="flex gap-2">
                  <ButtonUI
                    onClick={handleSaveEdit}
                    disabled={isSaving}
                    className="flex-1"
                  >
                    {isSaving ? "Сохранение..." : "Сохранить"}
                  </ButtonUI>
                  <ButtonUI
                    variant="secondary"
                    onClick={() => setEditingUser(null)}
                    className="flex-1"
                  >
                    Отмена
                  </ButtonUI>
                </div>
              </div>
            ) : (
              <div
                key={user.id}
                className="bg-white border border-gray-300 p-4"
              >
                <TextUI variant="normal" title={user.fullname}>
                  <span className="line-clamp-1">{user.fullname}</span>
                </TextUI>
                <TextUI variant="desc" className="mt-1">
                  {user.email}
                </TextUI>
                <TextUI variant="desc" className="mt-1">
                  {ROLE_LABELS[user.role] ?? user.role}
                </TextUI>
                <TextUI variant="desc" className="mt-1 line-clamp-2">
                  Навыки:{" "}
                  {Object.entries(skillsSetToLevels(user.skills_set))
                    .map(([name, level]) => `${name} (${level})`)
                    .join(", ") || "не указаны"}
                </TextUI>
                {isAdmin && (
                  <ButtonUI
                    variant="link"
                    onClick={() => startEdit(user)}
                    className="mt-2"
                  >
                    Изменить
                  </ButtonUI>
                )}
              </div>
            ),
          )}
        </div>
      )}
    </PageLayout>
  );
}
