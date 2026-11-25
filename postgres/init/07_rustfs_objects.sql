DROP TABLE IF EXISTS rustfs_objects CASCADE;
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
  rustfs_objects (
    id SERIAL PRIMARY KEY,
    object_key VARCHAR(128) UNIQUE NOT NULL,
    bucket VARCHAR(64) NOT NULL,
    extension VARCHAR(32) NOT NULL,
    size INT NOT NULL,
    status file_status NOT NULL DEFAULT 'not_extracted',
    feature_set JSONB NOT NULL DEFAULT '{}',
    model_version VARCHAR(64) NOT NULL DEFAULT '-'
  );

CREATE INDEX rustfs_objects_status_idx ON rustfs_objects (status);
