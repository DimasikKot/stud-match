CREATE EXTENSION IF NOT EXISTS pgcrypto; -- crypt()/gen_salt() для bcrypt-хеша пароля админа

CREATE TABLE users (
  id              SERIAL        PRIMARY KEY,
  email           VARCHAR (255) NOT NULL UNIQUE,
  hashed_password VARCHAR (255) NOT NULL,
  role            VARCHAR (20)  DEFAULT 'teacher' NOT NULL CHECK (role IN ('admin', 'teacher')),
  created_at      TIMESTAMP     DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at      TIMESTAMP     DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Администратор может быть только один
CREATE UNIQUE INDEX users_single_admin ON users (role) WHERE role = 'admin';

-- Администратор. Почту и пароль можно передать в контейнер postgres
-- переменными ADMIN_EMAIL / ADMIN_PASSWORD, иначе берутся значения ниже.
-- Пароль по умолчанию смените сразу после первого входа (PATCH /users/me/password).
\set admin_email 'admin@stud-match.ru'
\set admin_password 'admin'
\getenv admin_email ADMIN_EMAIL
\getenv admin_password ADMIN_PASSWORD

INSERT INTO users (email, hashed_password, role)
VALUES (:'admin_email', crypt(:'admin_password', gen_salt('bf', 12)), 'admin');

CREATE TABLE files (
  id         SERIAL        PRIMARY KEY,
  name       VARCHAR (255) NOT NULL,
  object_key VARCHAR (255) NOT NULL,
  path       VARCHAR (255) NOT NULL,
  size       INT           NOT NULL,
  created_at TIMESTAMP     DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at TIMESTAMP     DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE students (
  id            SERIAL        PRIMARY KEY,
  name          VARCHAR (255) NOT NULL,
  skills_vector JSONB         DEFAULT '{}' NOT NULL,
  description   TEXT          NOT NULL,
  created_at    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE projects (
  id            SERIAL        PRIMARY KEY,
  user_id       INT           NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  name          VARCHAR (255) NOT NULL,
  skills_vector JSONB         DEFAULT '{}' NOT NULL,
  description   TEXT          NOT NULL,
  created_at    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX projects_user_id_idx ON projects (user_id);

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

CREATE TABLE student_files (
  file_id    INT NOT NULL REFERENCES files (id) ON DELETE CASCADE,
  student_id INT NOT NULL REFERENCES students (id) ON DELETE CASCADE,
  PRIMARY KEY (file_id, student_id)
);

CREATE INDEX student_files_student_id_idx ON student_files (student_id);

-- История запросов к нейросети
CREATE TABLE llm_requests (
  id              SERIAL       PRIMARY KEY,
  task_id         VARCHAR (32) NOT NULL UNIQUE, -- id задачи в Redis
  user_id         INT          REFERENCES users (id) ON DELETE SET NULL,
  prompt          TEXT         NOT NULL,
  enable_thinking BOOLEAN      NOT NULL,
  max_new_tokens  INT          NOT NULL,
  status          VARCHAR (20) DEFAULT 'queued' NOT NULL CHECK (status IN ('queued', 'running', 'done', 'error')),
  result          TEXT,
  error           TEXT,
  created_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX llm_requests_user_id_idx ON llm_requests (user_id);

-- Файлы, использованные в запросе к нейросети
CREATE TABLE llm_request_files (
  request_id INT NOT NULL REFERENCES llm_requests (id) ON DELETE CASCADE,
  file_id    INT NOT NULL REFERENCES files (id) ON DELETE CASCADE,
  PRIMARY KEY (request_id, file_id)
);

CREATE INDEX llm_request_files_file_id_idx ON llm_request_files (file_id);