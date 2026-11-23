CREATE TYPE "user_role" AS ENUM ('admin', 'teacher');

CREATE TYPE "file_status" AS ENUM (
  'not_extracted',
  'queued',
  'extracting',
  'extracted',
  'applied'
);

CREATE TYPE "distribution_status" AS ENUM (
  'not_started',
  'queued',
  'distributing',
  'distributed'
);

CREATE TABLE
  "users" (
    "id" SERIAL PRIMARY KEY,
    "fullname" "VARCHAR(255)" NOT NULL,
    "email" "VARCHAR(255)" UNIQUE NOT NULL,
    "hashed_password" "VARCHAR(255)" NOT NULL,
    "role" user_role NOT NULL DEFAULT 'teacher',
    "skills_vector" JSONB NOT NULL DEFAULT '{}',
    "updated_at" TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP)
  );

-- Вставка админа с использованием переменных окружения
CREATE EXTENSION IF NOT EXISTS pgcrypto;

INSERT INTO
  users (email, hashed_password, role)
VALUES
  (
    '${ADMIN_EMAIL}',
    crypt ('${ADMIN_PASSWORD}', gen_salt ('bf', 12)),
    'admin'
  );

CREATE TABLE
  "files" (
    "id" SERIAL PRIMARY KEY,
    "name" "VARCHAR(255)" NOT NULL,
    "size" INT NOT NULL,
    "rustfs_object_key" "VARCHAR(255)" NOT NULL,
    "rustfs_bucket" "VARCHAR(255)" NOT NULL,
    "status" file_status NOT NULL DEFAULT 'not_extracted',
    "skills_vector" JSONB NOT NULL DEFAULT '{}',
    "work_date" TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP)
  );

CREATE TABLE
  "skills" (
    "id" SERIAL PRIMARY KEY,
    "name" "VARCHAR(255)" NOT NULL
  );

CREATE TABLE
  "students" (
    "id" SERIAL PRIMARY KEY,
    "fullname" "VARCHAR(255)" NOT NULL,
    "skills_vector" JSONB NOT NULL DEFAULT '{}'
  );

CREATE TABLE
  "student_files" (
    "file_id" INT NOT NULL,
    "student_id" INT NOT NULL,
    PRIMARY KEY ("file_id", "student_id")
  );

CREATE TABLE
  "projects" (
    "id" SERIAL PRIMARY KEY,
    "user_id" INT NOT NULL,
    "name" "VARCHAR(255)" NOT NULL,
    "description" TEXT NOT NULL,
    "constraints_vector" JSONB NOT NULL DEFAULT '{}',
    "skills_vector" JSONB NOT NULL DEFAULT '{}',
    "updated_at" TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP)
  );

CREATE TABLE
  "distributions" (
    "id" SERIAL PRIMARY KEY,
    "user_id" INT NOT NULL,
    "name" "VARCHAR(255)" NOT NULL,
    "status" distribution_status NOT NULL DEFAULT 'not_started',
    "selected_project_ids" JSONB NOT NULL DEFAULT '[]',
    "selected_student_ids" JSONB NOT NULL DEFAULT '[]',
    "selected_teacher_ids" JSONB NOT NULL DEFAULT '[]',
    "result" JSONB NOT NULL DEFAULT '{}',
    "updated_at" TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP)
  );

CREATE INDEX "student_files_student_id_idx" ON "student_files" ("student_id");

CREATE INDEX "projects_user_id_idx" ON "projects" ("user_id");

ALTER TABLE "projects" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "distributions" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "student_files" ADD FOREIGN KEY ("file_id") REFERENCES "files" ("id") ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "student_files" ADD FOREIGN KEY ("student_id") REFERENCES "students" ("id") ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;