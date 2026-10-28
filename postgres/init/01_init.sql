DROP TABLE IF EXISTS users;

CREATE TABLE
  users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
  );

DROP TABLE IF EXISTS entitys;

CREATE TABLE
  entitys (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(255) NOT NULL DEFAULT 'student' CHECK (type IN ('student', 
    'professor', 'project', 'teacher', 'course', 'group')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
  );

DROP TABLE IF EXISTS entitys_vectors;

CREATE TABLE
  entitys_vectors (
    id SERIAL PRIMARY KEY,
    entity_id INT NOT NULL,
    vector JSON DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
  );