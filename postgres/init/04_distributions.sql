DROP TABLE IF EXISTS distributions CASCADE;
DROP TYPE IF EXISTS distribution_status CASCADE;

CREATE TYPE distribution_status AS ENUM (
  'not_started',
  'queued',
  'distributing',
  'distributed',
  'failed'
);

CREATE TABLE
  distributions (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    status distribution_status NOT NULL DEFAULT 'not_started',
    selected_project_ids JSONB NOT NULL DEFAULT '[]',
    selected_student_ids JSONB NOT NULL DEFAULT '[]',
    selected_teacher_ids JSONB NOT NULL DEFAULT '[]',
    result_set JSONB NOT NULL DEFAULT '{}',
    model_version VARCHAR(255) NOT NULL DEFAULT '1.0.0',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
  );

CREATE INDEX distributions_user_id_idx ON distributions (user_id);

ALTER TABLE distributions ADD FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;
