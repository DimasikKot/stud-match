import { useEffect, useState } from "react";
import toast from "react-hot-toast";

import { fetchSkills, type SkillResponse } from "@/shared/api/skills";
import {
  createProject,
  deleteProject,
  fetchProject,
  fetchProjects,
  updateProject,
  type ProjectDetailResponse,
  type ProjectResponse,
} from "@/shared/api/projects";
import { PageLayout } from "@/shared/components/Layouts/PageLayout";
import { ButtonUI } from "@/shared/components/UI/ButtonUI";
import { InputUI } from "@/shared/components/UI/InputUI";
import { TextUI } from "@/shared/components/UI/TextUI";
import { SkillsPicker } from "@/shared/components/SkillsPicker";
import { skillsSetToLevels } from "@/shared/utils/skillsSet";

const emptyForm = {
  name: "",
  description: "",
  minStudents: "",
  maxStudents: "",
  skillLevels: {} as Record<string, number>,
};

const parseStudents = (value: string): number | null => {
  const trimmed = value.trim();
  if (!trimmed) return null;
  const parsed = Number.parseInt(trimmed, 10);
  return Number.isNaN(parsed) ? null : parsed;
};

export function Projects() {
  const [projects, setProjects] = useState<ProjectResponse[]>([]);
  const [skills, setSkills] = useState<SkillResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  const [showForm, setShowForm] = useState(false);
  const [editingProject, setEditingProject] =
    useState<ProjectDetailResponse | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    Promise.all([
      fetchProjects()
        .then((response) => setProjects(response.data))
        .catch(() => setHasError(true)),
      fetchSkills()
        .then((response) => setSkills(response.data))
        .catch(() => setSkills([])),
    ]).finally(() => setIsLoading(false));
  }, []);

  const reloadProjects = () =>
    fetchProjects()
      .then((response) => setProjects(response.data))
      .catch(() => setHasError(true));

  const openCreateForm = () => {
    setEditingProject(null);
    setForm(emptyForm);
    setShowForm(true);
  };

  const openEditForm = async (project: ProjectResponse) => {
    try {
      const detail = await fetchProject(project.id);
      const constraints = detail.constraints_set ?? {};
      setEditingProject(detail);
      setForm({
        name: detail.name,
        description: detail.description,
        minStudents:
          typeof constraints.min_students === "number"
            ? String(constraints.min_students)
            : "",
        maxStudents:
          typeof constraints.max_students === "number"
            ? String(constraints.max_students)
            : "",
        skillLevels: skillsSetToLevels(detail.skills_set),
      });
      setShowForm(true);
    } catch {
      // Ошибка уже показана через errorValidate
    }
  };

  const handleSave = async () => {
    if (!form.name.trim() || !form.description.trim()) {
      toast.error("Заполните название и описание");
      return;
    }

    const minStudents = parseStudents(form.minStudents);
    const maxStudents = parseStudents(form.maxStudents);
    if (
      minStudents !== null &&
      maxStudents !== null &&
      minStudents > maxStudents
    ) {
      toast.error("Минимум студентов не может быть больше максимума");
      return;
    }

    const payload = {
      name: form.name.trim(),
      description: form.description.trim(),
      constraints_set: {
        min_students: minStudents,
        max_students: maxStudents,
      },
      skills_set: form.skillLevels,
    };

    setIsSaving(true);
    try {
      if (editingProject) {
        await updateProject(editingProject.id, payload);
        toast.success("Проект обновлён");
      } else {
        await createProject(payload);
        toast.success("Проект создан");
      }
      setForm(emptyForm);
      setEditingProject(null);
      setShowForm(false);
      await reloadProjects();
    } catch {
      // Ошибка уже показана через errorValidate
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (projectId: number) => {
    try {
      await deleteProject(projectId);
      toast.success("Проект удалён");
      setProjects((prev) => prev.filter((project) => project.id !== projectId));
    } catch {
      // Ошибка уже показана через errorValidate
    }
  };

  return (
    <PageLayout title="Проекты">
      <div className="grid grid-cols-2 items-center justify-between mb-4">
        <TextUI variant="header">Проекты ({projects.length})</TextUI>

        <ButtonUI onClick={openCreateForm}>Создать проект</ButtonUI>
      </div>

      {showForm && (
        <div className="bg-white border border-gray-300 p-4 mb-6">
          <TextUI variant="subtitle" className="mb-3">
            {editingProject ? "Редактирование проекта" : "Новый проект"}
          </TextUI>

          <div className="flex flex-col gap-3 max-w-xl">
            <InputUI
              value={form.name}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, name: event.target.value }))
              }
              placeholder="Название проекта"
            />
            <InputUI
              value={form.description}
              onChange={(event) =>
                setForm((prev) => ({
                  ...prev,
                  description: event.target.value,
                }))
              }
              isArea
              rows={3}
              placeholder="Описание проекта"
            />

            <div className="flex gap-3">
              <div className="flex-1">
                <TextUI variant="label">Минимум студентов</TextUI>
                <InputUI
                  value={form.minStudents}
                  onChange={(event) =>
                    setForm((prev) => ({
                      ...prev,
                      minStudents: event.target.value,
                    }))
                  }
                  placeholder="Не задано"
                />
              </div>
              <div className="flex-1">
                <TextUI variant="label">Максимум студентов</TextUI>
                <InputUI
                  value={form.maxStudents}
                  onChange={(event) =>
                    setForm((prev) => ({
                      ...prev,
                      maxStudents: event.target.value,
                    }))
                  }
                  placeholder="Не задано"
                />
              </div>
            </div>

            <div>
              <TextUI variant="label">Навыки</TextUI>
              <SkillsPicker
                skills={skills}
                value={form.skillLevels}
                onChange={(levels) =>
                  setForm((prev) => ({ ...prev, skillLevels: levels }))
                }
              />
            </div>

            <div className="flex gap-2">
              <ButtonUI
                onClick={handleSave}
                disabled={isSaving}
                className="flex-1"
              >
                {isSaving ? "Сохранение..." : "Сохранить"}
              </ButtonUI>
              <ButtonUI
                variant="secondary"
                onClick={() => {
                  setShowForm(false);
                  setEditingProject(null);
                  setForm(emptyForm);
                }}
                className="flex-1"
              >
                Отмена
              </ButtonUI>
            </div>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="bg-white border border-gray-300 text-center">
          <TextUI variant="desc">Загрузка...</TextUI>
        </div>
      ) : hasError ? (
        <div className="bg-white border border-gray-300 text-center">
          <TextUI variant="desc">Не удалось загрузить список проектов</TextUI>
        </div>
      ) : projects.length === 0 ? (
        <div className="bg-white border border-gray-300 text-center">
          <TextUI variant="desc">Проектов пока нет</TextUI>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((project) => (
            <div
              key={project.id}
              className="bg-white border border-gray-300 p-4"
            >
              <TextUI variant="normal" title={project.name}>
                <span className="line-clamp-1">{project.name}</span>
              </TextUI>
              <TextUI variant="desc" className="mt-1 line-clamp-3">
                {project.description}
              </TextUI>
              <TextUI variant="desc" className="mt-1">
                Обновлён:{" "}
                {new Date(project.updated_at).toLocaleDateString("ru-RU")}
              </TextUI>
              <div className="flex gap-1 mt-2">
                <ButtonUI variant="link" onClick={() => openEditForm(project)}>
                  Изменить
                </ButtonUI>
                <ButtonUI
                  variant="link"
                  onClick={() => handleDelete(project.id)}
                >
                  Удалить
                </ButtonUI>
              </div>
            </div>
          ))}
        </div>
      )}
    </PageLayout>
  );
}
