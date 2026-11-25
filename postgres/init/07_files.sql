DROP TABLE IF EXISTS files CASCADE;
DROP TYPE IF EXISTS file_status CASCADE;

CREATE TYPE file_status AS ENUM (
  'not_extracted',
  'queued',
  'extracting',
  'extracted',
  'failed',
  'applied'
);

CREATE TABLE
  files (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    size INT NOT NULL,
    rustfs_object_key VARCHAR(255) NOT NULL,
    rustfs_bucket VARCHAR(255) NOT NULL,
    status file_status NOT NULL DEFAULT 'not_extracted',
    feature_set JSONB NOT NULL DEFAULT '{}',
    model_version VARCHAR(255) NOT NULL DEFAULT '1.0.0',
    zip_id INT NOT NULL
  );

CREATE INDEX files_zip_id_idx ON files (zip_id);
CREATE INDEX files_status_idx ON files (status);

ALTER TABLE files ADD FOREIGN KEY (zip_id) REFERENCES zips (id) ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;