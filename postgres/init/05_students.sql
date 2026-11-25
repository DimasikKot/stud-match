DROP TABLE IF EXISTS students CASCADE;

CREATE TABLE
  students (
    id SERIAL PRIMARY KEY,
    fullname VARCHAR(255) NOT NULL,
    skills_set JSONB NOT NULL DEFAULT '{}',
    model_version VARCHAR(255) NOT NULL DEFAULT '1.0.0'
  );
