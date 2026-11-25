CREATE TYPE "user_role" AS ENUM ('admin', 'teacher');

CREATE TYPE "zip_status" AS ENUM (
  'pending',
  'processing',
  'completed',
  'failed'
);

CREATE TYPE "file_status" AS ENUM (
  'not_extracted',
  'queued',
  'extracting',
  'extracted',
  'failed',
  'applied'
);

CREATE TYPE "distribution_status" AS ENUM (
  'not_started',
  'queued',
  'distributing',
  'distributed',
  'failed'
);

CREATE TABLE
  "users" (
    "id" SERIAL PRIMARY KEY,
    "fullname" "VARCHAR(255)" NOT NULL,
    "email" "VARCHAR(255)" UNIQUE NOT NULL,
    "hashed_password" "VARCHAR(255)" NOT NULL,
    "role" user_role NOT NULL DEFAULT 'teacher',
    "skills_set" JSONB NOT NULL DEFAULT '{}',
    "model_version" "VARCHAR(255)" NOT NULL DEFAULT '-',
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
  "zips" (
    "id" SERIAL PRIMARY KEY,
    "status" zip_status NOT NULL DEFAULT 'pending',
    "name" "VARCHAR(255)" NOT NULL,
    "date" TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP)
  );

CREATE TABLE
  "files" (
    "id" SERIAL PRIMARY KEY,
    "name" "VARCHAR(255)" NOT NULL,
    "size" INT NOT NULL,
    "rustfs_object_key" "VARCHAR(255)" NOT NULL,
    "rustfs_bucket" "VARCHAR(255)" NOT NULL,
    "status" file_status NOT NULL DEFAULT 'not_extracted',
    "skills_set" JSONB NOT NULL DEFAULT '{}',
    "model_version" "VARCHAR(255)" NOT NULL DEFAULT '-',
    "zip_id" INT NOT NULL
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
    "skills_set" JSONB NOT NULL DEFAULT '{}',
    "model_version" "VARCHAR(255)" NOT NULL DEFAULT '-'
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
    "constraints_set" JSONB NOT NULL DEFAULT '{}',
    "skills_set" JSONB NOT NULL DEFAULT '{}',
    "model_version" "VARCHAR(255)" NOT NULL DEFAULT '-',
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
    "result_set" JSONB NOT NULL DEFAULT '{}',
    "model_version" "VARCHAR(255)" NOT NULL DEFAULT '-',
    "updated_at" TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP)
  );

CREATE INDEX "files_status_idx" ON "files" ("status");
  
CREATE INDEX "files_zip_id_idx" ON "files" ("zip_id");

CREATE INDEX "files_rustfs_object_key_idx" ON "files" ("rustfs_object_key");

CREATE INDEX "student_files_student_id_idx" ON "student_files" ("student_id");

CREATE INDEX "projects_user_id_idx" ON "projects" ("user_id");

CREATE INDEX "distributions_user_id_idx" ON "distributions" ("user_id");

ALTER TABLE "projects" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "distributions" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "student_files" ADD FOREIGN KEY ("file_id") REFERENCES "files" ("id") ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "student_files" ADD FOREIGN KEY ("student_id") REFERENCES "students" ("id") ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "files" ADD FOREIGN KEY ("zip_id") REFERENCES "zips" ("id") ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;