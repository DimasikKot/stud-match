-- Файл можно перезапустить на живой БД (postgres/reinit.sh): он удаляет свои таблицы
-- и создаёт их заново. CASCADE снимает внешние ключи зависимых таблиц — reinit.sh
-- перезапустит и файлы, где они объявлены.

DROP TABLE IF EXISTS student_files, students CASCADE;

CREATE TABLE students (
  id            SERIAL        PRIMARY KEY,
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
