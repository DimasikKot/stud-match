CREATE TABLE users (
  id              SERIAL        PRIMARY KEY,
  email           VARCHAR (255) NOT NULL UNIQUE,
  hashed_password VARCHAR (255) NOT NULL,
  created_at      TIMESTAMP     DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at      TIMESTAMP     DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE files (
  id         SERIAL        PRIMARY KEY,
  name       VARCHAR (255) NOT NULL,
  object_key VARCHAR (255) NOT NULL,
  path       VARCHAR (255) NOT NULL,
  created_at TIMESTAMP     DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at TIMESTAMP     DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE students (
  id            SERIAL        PRIMARY KEY,
  name          VARCHAR (255) NOT NULL,
  skills_vector JSON          DEFAULT '{}',
  description   TEXT          NOT NULL,
  created_at    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE projects (
  id            SERIAL        PRIMARY KEY,
  user_id       INT           NOT NULL,
  name          VARCHAR (255) NOT NULL,
  skills_vector JSON          DEFAULT '{}',
  description   TEXT          NOT NULL,
  created_at    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE teachers (
  id            SERIAL        PRIMARY KEY,
  name          VARCHAR (255) NOT NULL,
  skills_vector JSON          DEFAULT '{}',
  description   TEXT          NOT NULL,
  created_at    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE student_files (
  file_id    INT FOREIGN KEY REFERENCES files (id) ON DELETE CASCADE,
  student_id INT FOREIGN KEY REFERENCES students (id) ON DELETE CASCADE,
  PRIMARY KEY (file_id, student_id)
);