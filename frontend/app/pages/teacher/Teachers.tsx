import { useEffect, useState } from "react";

import { TextUI } from "@/shared/components/UI/TextUI";
import { PageLayout } from "@/shared/components/Layouts/PageLayout";
import { fetchUsers, type UserResponse } from "@/shared/api/users";

const ROLE_LABELS: Record<string, string> = {
  admin: "Администратор",
  teacher: "Преподаватель",
};

export default function Teachers() {
  const [users, setUsers] = useState<UserResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    fetchUsers()
      .then((response) => setUsers(response.data))
      .catch(() => setHasError(true))
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <PageLayout title="Преподаватели">
      <TextUI variant="header" className="mb-4">
        Преподаватели ({users.length})
      </TextUI>

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
          {users.map((user) => (
            <div key={user.id} className="bg-white border border-gray-300 p-4">
              <TextUI variant="normal" title={user.fullname}>
                <span className="line-clamp-1">{user.fullname}</span>
              </TextUI>
              <TextUI variant="desc" className="mt-1">
                {user.email}
              </TextUI>
              <TextUI variant="desc" className="mt-1">
                {ROLE_LABELS[user.role] ?? user.role}
              </TextUI>
            </div>
          ))}
        </div>
      )}
    </PageLayout>
  );
}
