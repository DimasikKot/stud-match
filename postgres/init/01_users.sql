-- Файл можно перезапустить на живой БД (postgres/reinit.sh): он удаляет свои таблицы
-- и создаёт их заново. CASCADE снимает внешние ключи зависимых таблиц — reinit.sh
-- перезапустит и файлы, где они объявлены.

DROP TABLE IF EXISTS users CASCADE;

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
