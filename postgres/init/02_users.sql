DROP TABLE IF EXISTS users CASCADE;
DROP TYPE IF EXISTS user_role CASCADE;

CREATE TYPE user_role AS ENUM ('admin', 'teacher');

CREATE TABLE
  users (
    id SERIAL PRIMARY KEY,
    fullname VARCHAR(256) NOT NULL,
    email VARCHAR(256) UNIQUE NOT NULL,
    hashed_password VARCHAR(1024) NOT NULL,
    role user_role NOT NULL DEFAULT 'teacher',
    skills_set JSONB NOT NULL DEFAULT '{}',
    model_version VARCHAR(64) NOT NULL DEFAULT '-',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
  );

-- Вставка админа с использованием переменных окружения
CREATE EXTENSION IF NOT EXISTS pgcrypto;

INSERT INTO users (fullname, email, hashed_password, role)
VALUES (
    'Администратор',
    '${ADMIN_EMAIL}',
    crypt('${ADMIN_PASSWORD}', gen_salt('bf', 12)),
    'admin'
);
