-- Реинит: сбрасываем таблицу перед созданием (скрипт идемпотентен)
DROP TABLE IF EXISTS users CASCADE;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- crypt()/gen_salt() для bcrypt-хеша пароля админа
CREATE TABLE
  users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'teacher' NOT NULL CHECK (role IN ('admin', 'teacher')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
  );

-- Администратор может быть только один
CREATE UNIQUE INDEX users_single_admin ON users (role)
WHERE
  role = 'admin';

/*
INSERT INTO users (email, hashed_password, role)
VALUES (
'localhost@stud-match.ru',
crypt('localhost_password', gen_salt('bf', 12)),
'admin'
);
 */
