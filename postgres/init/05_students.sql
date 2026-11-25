DROP TABLE IF EXISTS students CASCADE;

CREATE TABLE
  students (
    id SERIAL PRIMARY KEY,
    fullname VARCHAR(256) NOT NULL,
    skills_set JSONB NOT NULL DEFAULT '{}',
    model_version VARCHAR(64) NOT NULL DEFAULT '-'
  );
