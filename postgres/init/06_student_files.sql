-- Реинит: сбрасываем таблицу перед созданием (скрипт идемпотентен)
DROP TABLE IF EXISTS student_files CASCADE;

CREATE TABLE
  student_files (
    file_id INT NOT NULL REFERENCES files (id) ON DELETE CASCADE,
    student_id INT NOT NULL REFERENCES students (id) ON DELETE CASCADE,
    PRIMARY KEY (file_id, student_id)
  );

CREATE INDEX student_files_student_id_idx ON student_files (student_id);
