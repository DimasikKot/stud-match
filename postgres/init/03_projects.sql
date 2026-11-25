DROP TABLE IF EXISTS projects CASCADE;

CREATE TABLE
  projects (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    constraints_set JSONB NOT NULL DEFAULT '{}',
    skills_set JSONB NOT NULL DEFAULT '{}',
    model_version VARCHAR(255) NOT NULL DEFAULT '-',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
  );

CREATE INDEX projects_user_id_idx ON projects (user_id);

ALTER TABLE projects ADD FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;