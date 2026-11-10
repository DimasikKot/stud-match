-- Реинит: сбрасываем таблицу перед созданием (скрипт идемпотентен)
DROP TABLE IF EXISTS llm_requests CASCADE;

-- История запросов к нейросети
CREATE TABLE
  llm_requests (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(32) NOT NULL UNIQUE, -- id задачи в Redis
    user_id INT REFERENCES users (id) ON DELETE SET NULL,
    prompt TEXT NOT NULL,
    enable_thinking BOOLEAN NOT NULL,
    max_new_tokens INT NOT NULL,
    status VARCHAR(20) DEFAULT 'queued' NOT NULL CHECK (status IN ('queued', 'running', 'done', 'error')),
    result TEXT,
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
  );

CREATE INDEX llm_requests_user_id_idx ON llm_requests (user_id);
