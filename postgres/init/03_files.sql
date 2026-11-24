DROP TABLE IF EXISTS files CASCADE;
DROP TYPE IF EXISTS file_status CASCADE;

CREATE TYPE file_status AS ENUM (
  'not_extracted',
  'queued',
  'extracting',
  'extracted',
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
    skills_vector JSONB NOT NULL DEFAULT '{}',
    work_zip_id INT NOT NULL
  );

CREATE INDEX files_work_zip_id_idx ON files (work_zip_id);

ALTER TABLE files ADD FOREIGN KEY (work_zip_id) REFERENCES work_zips (id) ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;