-- Реинит: сбрасываем таблицу перед созданием (скрипт идемпотентен)
DROP TABLE IF EXISTS llm_request_files CASCADE;

-- Файлы, использованные в запросе к нейросети
CREATE TABLE
  llm_request_files (
    request_id INT NOT NULL REFERENCES llm_requests (id) ON DELETE CASCADE,
    file_id INT NOT NULL REFERENCES files (id) ON DELETE CASCADE,
    PRIMARY KEY (request_id, file_id)
  );

CREATE INDEX llm_request_files_file_id_idx ON llm_request_files (file_id);
