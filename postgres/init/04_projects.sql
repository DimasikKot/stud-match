-- Реинит: сбрасываем таблицу перед созданием (скрипт идемпотентен)
DROP TABLE IF EXISTS projects CASCADE;

CREATE TABLE
  projects (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    skills_vector JSONB DEFAULT '{}' NOT NULL,
    description TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
  );

CREATE INDEX projects_user_id_idx ON projects (user_id);
