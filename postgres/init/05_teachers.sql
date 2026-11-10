-- Файл можно перезапустить на живой БД (postgres/reinit.sh): он удаляет свои таблицы
-- и создаёт их заново. CASCADE снимает внешние ключи зависимых таблиц — reinit.sh
-- перезапустит и файлы, где они объявлены.

DROP TABLE IF EXISTS teachers CASCADE;

-- Профиль преподавателя, привязан к учётной записи пользователя (1 к 1)
CREATE TABLE teachers (
  id            SERIAL        PRIMARY KEY,
  user_id       INT           UNIQUE REFERENCES users (id) ON DELETE CASCADE,
  name          VARCHAR (255) NOT NULL,
  skills_vector JSONB         DEFAULT '{}' NOT NULL,
  description   TEXT          NOT NULL,
  created_at    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP NOT NULL
);
