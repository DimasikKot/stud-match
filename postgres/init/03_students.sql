-- Реинит: сбрасываем таблицу перед созданием (скрипт идемпотентен)
DROP TABLE IF EXISTS students CASCADE;

CREATE TABLE
  students (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    skills_vector JSONB DEFAULT '{}' NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
  );
