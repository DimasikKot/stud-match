import { useEffect, useState } from "react";

import { TextUI } from "@/shared/components/UI/TextUI";
import { PageLayout } from "@/shared/components/Layouts/PageLayout";
import { fetchProjects, type ProjectResponse } from "@/shared/api/projects";

export function Projects() {
  const [projects, setProjects] = useState<ProjectResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    fetchProjects()
      .then((response) => setProjects(response.data))
      .catch(() => setHasError(true))
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <PageLayout title="Проекты">
      <TextUI variant="header" className="mb-4">
        Проекты ({projects.length})
      </TextUI>

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
            </div>
          ))}
        </div>
      )}
    </PageLayout>
  );
}
